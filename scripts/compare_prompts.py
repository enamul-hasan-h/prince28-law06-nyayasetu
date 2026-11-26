"""Compare classification prompt versions against the fixed evaluation test set."""

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

from nyayasetu.config import get_settings
from nyayasetu.db.llm_calls import make_recorder
from nyayasetu.db.session import SessionLocal, engine
from nyayasetu.llm.classify import LABELS, accuracy, classify, find_leaks
from nyayasetu.llm.gateway import LLMUnavailable, build_gateway
from nyayasetu.llm.prompts import read_prompt, versions

TESTSET = Path("eval/prompt_testset.jsonl")
CACHE = Path("eval/cache/classify.json")
NOTES = Path("NOTES.md")
START = "<!-- prompts:start -->"
END = "<!-- prompts:end -->"


def load_testset() -> tuple[list[dict], int]:
    """Load valid labelled examples and count TODO placeholders."""
    if not TESTSET.exists():
        raise FileNotFoundError(f"Test set not found: {TESTSET}")

    examples = []
    todo_count = 0

    for line_number, line in enumerate(TESTSET.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue

        row = json.loads(line)
        question = str(row.get("question", "")).strip()
        label = row.get("label")

        if "TODO" in question.upper():
            todo_count += 1
            continue

        if not question:
            raise ValueError(f"Empty question on line {line_number}")
        if label not in LABELS:
            raise ValueError(f"Invalid label on line {line_number}: {label!r}")

        examples.append(
            {
                "line": line_number,
                "question": question,
                "label": label,
            }
        )

    if not examples:
        raise ValueError("No valid questions found in the test set.")

    return examples, todo_count


def cache_key(prompt: str, question: str) -> str:
    content = f"{prompt}\n---QUESTION---\n{question}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_table(results: list[dict], todo_count: int) -> None:
    lines = [
        START,
        "## Prompt comparison",
        "",
        f"Evaluation set: {len(results[0]['rows']) if results else 0} questions. "
        f"TODO placeholders skipped: {todo_count}.",
        "",
        "| Prompt version | Correct | Accuracy | Invalid replies | Avg tokens in |",
        "|---|---:|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            f"| `{result['version']}` "
            f"| {result['correct']}/{result['total']} "
            f"| {result['accuracy']:.1%} "
            f"| {result['invalid']} "
            f"| {result['avg_tokens_in']:.1f} |"
        )

    lines.extend(["", END])
    section = "\n".join(lines)

    existing = NOTES.read_text(encoding="utf-8") if NOTES.exists() else ""

    if START in existing and END in existing:
        before = existing.split(START, 1)[0]
        after = existing.split(END, 1)[1]
        updated = before + section + after
    else:
        if START in existing or END in existing:
            raise ValueError(
                "NOTES.md contains only one comparison marker. "
                "Please inspect it before changing the file."
            )
        updated = existing.rstrip() + "\n\n" + section + "\n"

    NOTES.write_text(updated, encoding="utf-8")


async def run(rpm: float, no_cache: bool) -> int:
    settings = get_settings()
    examples, todo_count = load_testset()

    prompt_versions = versions(settings.prompts_dir, "classify")
    if not prompt_versions:
        raise FileNotFoundError(f"No classify_v*.md prompts found in {settings.prompts_dir}")

    if no_cache:
        cache = {}
    elif CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        cache = {}

    if not isinstance(cache, dict):
        raise ValueError("The classification cache must contain a JSON object.")

    prompts = []
    for version in prompt_versions:
        prompt = read_prompt(settings.prompts_dir, version)

        if "TODO" in prompt.upper():
            print(f"Skipping {version}: TODO placeholder found.")
            continue

        leaks = find_leaks(
            prompt,
            [example["question"] for example in examples],
        )
        for question in leaks:
            print(f"LEAK: {version} contains test question: {question}")

        prompts.append((version, prompt))

    if not prompts:
        raise ValueError("No usable classification prompts found.")

    jobs = []
    for version, prompt in prompts:
        for example in examples:
            key = cache_key(prompt, example["question"])
            jobs.append((version, prompt, example, key))

    missing_keys = {key for _, _, _, key in jobs if key not in cache}
    total_new_calls = len(missing_keys)

    print(f"Questions: {len(examples)}")
    print(f"Prompt versions: {len(prompts)}")
    print(f"Cached results: {len(jobs) - sum(key not in cache for _, _, _, key in jobs)}")
    print(f"New model calls required: {total_new_calls}")
    print(f"Rate limit: {rpm:g} calls/minute")
    print()

    gateway = build_gateway(settings, make_recorder(SessionLocal))
    results = []
    calls_made = 0

    try:
        for version, prompt, example, key in jobs:
            question = example["question"]

            if key in cache:
                cached = cache[key]
                got = cached["got"]
                tokens_in = int(cached.get("tokens_in", 0))
            else:
                print(
                    f"[{calls_made + 1}/{total_new_calls}] "
                    f"{version} | test-set line {example['line']}"
                )

                try:
                    got, reply = await classify(gateway, prompt, version, question)
                except LLMUnavailable as exc:
                    print(f"\nLLM unavailable: {exc}", file=sys.stderr)
                    return 1

                tokens_in = reply.tokens_in
                cache[key] = {
                    "got": got,
                    "tokens_in": tokens_in,
                    "reply": reply.text[:300],
                }
                save_cache(cache)
                calls_made += 1

                if calls_made < total_new_calls:
                    await asyncio.sleep(60 / rpm)

            row = {
                "question": question,
                "label": example["label"],
                "got": got,
                "tokens_in": tokens_in,
            }

            version_result = next(
                (item for item in results if item["version"] == version),
                None,
            )
            if version_result is None:
                version_result = {
                    "version": version,
                    "rows": [],
                }
                results.append(version_result)

            version_result["rows"].append(row)

        for result in results:
            rows = result["rows"]
            correct = sum(row["got"] == row["label"] for row in rows)
            invalid = sum(row["got"] == "invalid" for row in rows)
            avg_tokens = sum(row["tokens_in"] for row in rows) / len(rows) if rows else 0

            result["correct"] = correct
            result["total"] = len(rows)
            result["accuracy"] = accuracy(rows)
            result["invalid"] = invalid
            result["avg_tokens_in"] = avg_tokens

        write_table(results, todo_count)

        print("\n--- Comparison results ---")
        for result in results:
            print(
                f"{result['version']}: "
                f"{result['correct']}/{result['total']} correct "
                f"({result['accuracy']:.1%}), "
                f"{result['invalid']} invalid, "
                f"average input tokens={result['avg_tokens_in']:.1f}"
            )

            misses = [row for row in result["rows"] if row["got"] != row["label"]]
            for miss in misses:
                print(f"  MISS | expected={miss['label']} got={miss['got']} | {miss['question']}")

        print(f"\nNew model calls made: {calls_made}")
        print(f"Cache saved: {CACHE}")
        print(f"Comparison table updated: {NOTES}")

        return 0

    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare classification prompt versions.")
    parser.add_argument(
        "--rpm",
        type=float,
        default=12,
        help="Maximum fresh model calls per minute (default: 12).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore existing cached results and rerun every comparison.",
    )
    args = parser.parse_args()

    if args.rpm <= 0:
        parser.error("--rpm must be greater than zero.")

    raise SystemExit(asyncio.run(run(args.rpm, args.no_cache)))


if __name__ == "__main__":
    main()
