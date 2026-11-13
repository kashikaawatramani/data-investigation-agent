import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def save_evidence(tool_name, inputs, result):
    project_folder = Path(__file__).resolve().parent
    database_path = project_folder / "sales_demo.db"

    # Identify the exact database file used.
    database_hash = hashlib.sha256()

    with database_path.open("rb") as database_file:
        for chunk in iter(
            lambda: database_file.read(1024 * 1024), b""
        ):
            database_hash.update(chunk)

    evidence_id = str(uuid4())

    record = {
        "evidence_id": evidence_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "inputs": inputs,
        "database": database_path.name,
        "database_sha256": database_hash.hexdigest(),
        "result": result,
    }

    evidence_folder = project_folder / "evidence"
    evidence_folder.mkdir(exist_ok=True)

    evidence_path = evidence_folder / f"{evidence_id}.json"

    with evidence_path.open(
        "x", encoding="utf-8"
    ) as evidence_file:
        json.dump(record, evidence_file, indent=2)

    return {
        "evidence_id": evidence_id,
        "file": str(evidence_path),
    }