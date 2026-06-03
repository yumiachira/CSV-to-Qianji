import csv
from pathlib import Path
from typing import List

from py.config import CSV_FILE

CSV_HEADER = ["name", "type1", "type2"]


def _get_csv_path() -> Path:
    return Path(CSV_FILE)


def read_table_csv() -> List[dict]:
    path = _get_csv_path()
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [
            {
                "name": (row.get("name") or "").strip(),
                "type1": (row.get("type1") or "").strip(),
                "type2": (row.get("type2") or "").strip(),
            }
            for row in reader
            if row
        ]
    return rows


def write_table_csv(rows: List[dict]) -> None:
    path = _get_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "name": row.get("name", "").strip(),
                "type1": row.get("type1", "").strip(),
                "type2": row.get("type2", "").strip(),
            })


def add_entry(name: str, type1: str, type2: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("name 不能为空")
    rows = read_table_csv()
    exists = False
    for row in rows:
        if row["name"] == name:
            row["type1"] = type1.strip()
            row["type2"] = type2.strip()
            exists = True
            break
    if not exists:
        rows.append({"name": name, "type1": type1.strip(), "type2": type2.strip()})
    write_table_csv(rows)


def edit_entry(name: str, type1: str, type2: str) -> bool:
    name = name.strip()
    if not name:
        raise ValueError("name 不能为空")
    rows = read_table_csv()
    updated = False
    for row in rows:
        if row["name"] == name:
            row["type1"] = type1.strip()
            row["type2"] = type2.strip()
            updated = True
            break
    if updated:
        write_table_csv(rows)
    return updated


def delete_entry(name: str) -> bool:
    name = name.strip()
    if not name:
        raise ValueError("name 不能为空")
    rows = read_table_csv()
    filtered = [row for row in rows if row["name"] != name]
    if len(filtered) == len(rows):
        return False
    write_table_csv(filtered)
    return True


def search_entries(query: str = "") -> List[dict]:
    query_text = (query or "").strip().lower()
    rows = read_table_csv()
    if not query_text:
        return rows
    return [
        row for row in rows
        if query_text in row["name"].lower()
        or query_text in row["type1"].lower()
        or query_text in row["type2"].lower()
    ]


def sync_db() -> None:
    import insertSQL

    insertSQL.runsql()
