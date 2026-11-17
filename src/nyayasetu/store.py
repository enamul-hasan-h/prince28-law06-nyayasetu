"""Small in-memory store for document records loaded from a JSON file."""

import json
from pathlib import Path
from typing import Any


class RecordStore:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self._records: dict[str, dict[str, Any]] = {}
        self.ready = False

    def load(self) -> None:
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        with self.data_file.open("r", encoding="utf-8") as file:
            rows = json.load(file)

        if not isinstance(rows, list):
            raise ValueError("The data file must contain a JSON list.")

        records: dict[str, dict[str, Any]] = {}

        for row in rows:
            if not isinstance(row, dict) or "id" not in row:
                raise ValueError("Every record must be an object with an 'id'.")

            record_id = str(row["id"])
            records[record_id] = row

        self._records = records
        self.ready = True

    def search(self, q: str = "") -> list[dict[str, Any]]:
        query = q.strip().lower()

        if not query:
            return list(self._records.values())

        return [
            record
            for record in self._records.values()
            if query in json.dumps(record, ensure_ascii=False).lower()
        ]

    def get(self, record_id: str) -> dict[str, Any] | None:
        return self._records.get(record_id)
