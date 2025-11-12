# import_table_single.py
import csv,sqlite3
from py.config import DB_PATH,CSV_FILE,CSV_CREATE_TABLE_SQL

conn = sqlite3.connect(DB_PATH)
conn.executescript(CSV_CREATE_TABLE_SQL)

# 用 utf-8-sig 兼容带BOM的CSV
with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)  # 期望表头：name,type1,type2
    rows = [(r["name"].strip(), r["type1"].strip(), r["type2"].strip()) for r in reader]

# 插入（有同名则覆盖）
conn.executemany(
    "INSERT OR REPLACE INTO merchant_catalog(name,type1,type2) VALUES (?,?,?)",
    rows
)
conn.commit()
conn.close()

print("✅ 已导入 merchant_catalog 到", DB_PATH)