import pytest
from pydantic import ValidationError

from nyayasetu.llm.doc_meta import DocMeta
from nyayasetu.llm.extract import extract, parse_json, run
from nyayasetu.llm.gateway import FakeLLM, LLMGateway


def good(**changes):
    return {
        "doc_kind": "guideline",
        "year": 2024,
        "language": "en",
        "summary": "Explains eligibility and access to free legal aid services.",
        "topics": ["Legal aid"],
        **changes,
    }


def model_saying(*replies):
    llm = FakeLLM(script=list(replies))
    return llm, LLMGateway([llm])


def test_doc_meta_is_a_strict_contract():
    record = DocMeta.model_validate(good())
    assert record.doc_kind == "guideline"
    assert record.scheme == []
    assert record.section == []


def test_doc_meta_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        DocMeta.model_validate(good(surprise="extra"))


def test_doc_meta_rejects_invalid_kind():
    with pytest.raises(ValidationError):
        DocMeta.model_validate(good(doc_kind="judgment"))


def test_parse_json_extracts_object_from_wrapped_reply():
    assert parse_json('Result: {"year": 2024} Done') == {"year": 2024}


def test_parse_json_rejects_non_object():
    with pytest.raises(ValueError):
        parse_json("null")


@pytest.mark.asyncio
async def test_extract_accepts_valid_json():
    llm, gateway = model_saying(__import__("json").dumps(good()))
    result = await extract(
        gateway,
        DocMeta,
        "Extract metadata.",
        "extract_v1",
        "Test document",
        "Document text",
    )
    assert result.record is not None
    assert result.attempts == 1
    assert llm.calls == 1


@pytest.mark.asyncio
async def test_extract_repairs_invalid_reply():
    import json

    llm, gateway = model_saying(
        '{"doc_kind":"invalid"}',
        json.dumps(good()),
    )
    result = await extract(
        gateway,
        DocMeta,
        "Extract metadata.",
        "extract_v1",
        "Test document",
        "Document text",
    )
    assert result.record is not None
    assert result.attempts == 2
    assert result.errors


@pytest.mark.asyncio
async def test_extract_fails_after_max_attempts():
    llm, gateway = model_saying("not json", "still not json")
    result = await extract(
        gateway,
        DocMeta,
        "Extract metadata.",
        "extract_v1",
        "Test document",
        "Document text",
        max_attempts=2,
    )
    assert result.record is None
    assert result.attempts == 2
    assert len(result.errors) == 2


@pytest.mark.asyncio
async def test_run_rejects_reserved_schema_fields():
    class BadSchema(DocMeta):
        source: str

    llm, gateway = model_saying("{}")

    with pytest.raises(ValueError, match="parser already uses them"):
        await run(
            None,
            gateway,
            BadSchema,
            "Extract metadata.",
            "extract_v1",
        )
