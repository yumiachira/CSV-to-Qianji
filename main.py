from pathlib import Path
import csv
import insertSQL
import py.app_saizon as app_saizon
import py.app_epos as app_epos
import py.app_paypay as app_paypay
from py.common import normalize_date
from py.config import (
    DATE_COL_CANDIDATES,
    SAIZON_HEADER_SAIZON,
    PAYPAY_HEADER_SAIZON,
    EPOS_HEADER_SAIZON,
    ENCODING,
    INPUT_DIR,
    OUTPUT_DIR
    )

def detect_type(headers):
    """根据表头判断账单类型，返回 (type_name, handler, human_label)"""
    if headers == SAIZON_HEADER_SAIZON:
        return "saizon", app_saizon.outputCSV, "セゾン"
    if headers == PAYPAY_HEADER_SAIZON:
        return "paypay", app_paypay.outputCSV, "PAYPAY"
    if headers == EPOS_HEADER_SAIZON:
        return "epos", app_epos.outputCSV, "EPOS"
    return None, None, None

def find_date_col(headers):
    """从 headers 中找出日期列名和索引，没有则返回 (None, -1)"""
    for col in DATE_COL_CANDIDATES:
        if col in headers:
            return col, headers.index(col)
    return None, -1

def process_file(csv_file: Path):
    """处理单个 CSV 文件"""
    print(f"\n正在处理: {csv_file}")

    with csv_file.open("r", encoding=ENCODING, newline="") as f:
        reader = csv.reader(f)

        # 1. 读取表头
        try:
            headers = next(reader)
        except StopIteration:
            print("⚠️ 文件为空，跳过")
            return

        headers = [h.strip() for h in headers]

        # 2. 判定账单类型
        type_name, handler, label = detect_type(headers)
        if not type_name:
            print("⚠️ 未匹配到已知的账单表头，跳过")
            return
        print(f"检测到 {label} 账单格式")

        # 3. 查找日期列
        date_col_name, date_idx = find_date_col(headers)
        if date_col_name is None:
            print("⚠️ 未找到日期列（利用日 / 利用日/キャンセル日 / ご利用年月日），跳过")
            return
        print(f"检测到日期列: {date_col_name}（索引: {date_idx}）")

        # 4. 数据行（跳过空行）
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if not rows:
            print("⚠️ 没有数据行（只有表头），跳过")
            return

        # 第一条明细
        first_row = rows[0]
        first_raw = first_row[date_idx] if len(first_row) > date_idx else ""
        first_date = normalize_date(first_raw)

        # 最后一条明细
        last_row = rows[-1]
        last_raw = last_row[date_idx] if len(last_row) > date_idx else ""
        last_date = normalize_date(last_raw)

        if not first_date or not last_date:
            print(f"⚠️ 无法规范化日期（first={first_raw}, last={last_raw}），跳过")
            return

        print(f"第一行日期: {first_date}")
        print(f"最后一行日期: {last_date}")

        # 5. 生成输出路径
        output_path = Path(OUTPUT_DIR) / f"output_{type_name}_{first_date}-{last_date}.csv"
        print(f"输出文件: {output_path}")

        # 6. 调用对应 app 的输出函数
        handler(str(csv_file), str(output_path))

def run():
    """入口函数：扫描 input 下所有 csv 并处理"""

    insertSQL.runsql()

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    csv_paths = list(Path(INPUT_DIR).glob("*.csv"))
    if not csv_paths:
        print("⚠️ 没有找到任何 CSV 文件")
        return

    for csv_file in csv_paths:
        try:
            process_file(csv_file)
        except Exception as e:
            # 防止一个文件异常把整个流程弄崩
            print(f"⚠️ 处理文件 {csv_file} 时出错: {e}")

if __name__ == "__main__":
    run()