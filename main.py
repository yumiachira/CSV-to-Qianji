from pathlib import Path
import csv
import os
import sys
# 如果是 exe 运行，切换到项目根目录
if getattr(sys, "frozen", False):
    os.chdir(Path(sys.executable).parent.parent)
print("当前目录:", os.getcwd())

import insertSQL
import py.app_saizon as app_saizon
import py.app_epos as app_epos
import py.app_paypay as app_paypay
import chardet
import webbrowser
import web_update_db
from py.common import normalize_date
from py.config import (
    DATE_COL_CANDIDATES,
    SAIZON_HEADER_SAIZON,
    PAYPAY_HEADER_SAIZON,
    EPOS_HEADER_SAIZON,
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

def process_file(csv_file: Path, check_only=False):
    # 跳过临时清洗文件
    if csv_file.name.startswith("__cleaned_"):
        return []

    print(f"\n正在处理: {csv_file}")

    # 0. 自动检测编码
    with csv_file.open("rb") as fb:
        raw = fb.read()
        enc = chardet.detect(raw)["encoding"] or "cp932"

    with csv_file.open("r", encoding=enc, newline="") as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    if not all_rows:
        print("⚠️ 文件为空，跳过")
        return []

    # 1. 自动寻找真正的表头行
    header_idx = None
    headers = None
    type_name = None
    handler = None
    label = None

    for i, row in enumerate(all_rows[:20]):
        temp_headers = [h.strip() for h in row]

        tmp_type_name, tmp_handler, tmp_label = detect_type(temp_headers)

        if tmp_type_name:
            header_idx = i
            headers = temp_headers
            type_name = tmp_type_name
            handler = tmp_handler
            label = tmp_label
            break

    if header_idx is None:
        print("⚠️ 未匹配到已知的账单表头，跳过")
        return []

    print(f"检测到 {label} 账单格式")
    print(f"表头行位置: 第 {header_idx + 1} 行")

    # 2. 查找日期列
    date_col_name, date_idx = find_date_col(headers)
    if date_col_name is None:
        print("⚠️ 未找到日期列（利用日 / 利用日/キャンセル日 / ご利用年月日），跳过")
        return []

    print(f"检测到日期列: {date_col_name}（索引: {date_idx}）")

    # 3. 数据行：从真实表头下一行开始
    rows = []

    skip_keywords = [
        "合計",
        "※",
        "（＊",
        "円換算レート",
        "セゾン投信(株"
    ]

    for row in all_rows[header_idx + 1:]:

        # 空行跳过
        if not any(cell.strip() for cell in row):
            continue

        # 整行拼接成字符串用于判断
        row_text = ",".join(cell.strip() for cell in row)

        # 合计行、说明行、汇率说明行跳过
        if any(keyword in row_text for keyword in skip_keywords):
            continue

        raw_date = row[date_idx] if len(row) > date_idx else ""
        norm_date = normalize_date(raw_date)

        # 没有日期的跳过
        if not norm_date:
            continue

        rows.append(row)

    if not rows:
        print("⚠️ 没有有效明细行，跳过")
        return []

    # 4. 第一条明细日期
    first_row = rows[0]
    first_raw = first_row[date_idx] if len(first_row) > date_idx else ""
    first_date = normalize_date(first_raw)

    # 5. 最后一条明细日期
    last_row = rows[-1]
    last_raw = last_row[date_idx] if len(last_row) > date_idx else ""
    last_date = normalize_date(last_raw)

    if not first_date or not last_date:
        print(f"⚠️ 无法规范化日期（first={first_raw}, last={last_raw}），跳过")
        return []

    print(f"第一行日期: {first_date}")
    print(f"最后一行日期: {last_date}")

    # 6. 生成输出路径
    output_path = Path(OUTPUT_DIR) / f"output_{type_name}_{first_date}-{last_date}.csv"
    print(f"输出文件: {output_path}")

    # 7. 生成临时清洗版 CSV
    cleaned_path = csv_file.parent / f"__cleaned_{csv_file.name}"

    with cleaned_path.open("w", encoding="utf-8-sig", newline="") as wf:
        writer = csv.writer(wf)

        # 写表头
        writer.writerow(headers)

        # 写过滤后的有效数据
        writer.writerows(rows)

    # 8. 调用对应 app 的输出函数
    try:
        pending = handler(str(cleaned_path), str(output_path), check_only=check_only)
    finally:
        # 9. 删除临时文件
        try:
            cleaned_path.unlink()
        except Exception:
            pass

    return pending or []

def get_csv_paths():
    csv_paths = list(Path(INPUT_DIR).glob("*.csv"))

    if not csv_paths:
        print("⚠️ 没有找到任何 CSV 文件")

    return csv_paths


def check_pending():
    """只检查是否有默认分类，不生成 CSV"""
    csv_paths = get_csv_paths()
    all_pending = []

    for csv_file in csv_paths:
        try:
            all_pending.extend(process_file(csv_file, check_only=True))
        except Exception as e:
            print(f"⚠️ 检查文件 {csv_file} 时出错: {e}")

    return list(dict.fromkeys(all_pending))


def generate_csv():
    """正式生成 CSV"""
    csv_paths = get_csv_paths()

    for csv_file in csv_paths:
        try:
            process_file(csv_file, check_only=False)
        except Exception as e:
            print(f"⚠️ 处理文件 {csv_file} 时出错: {e}")


def run():
    """入口函数：扫描 input 下所有 csv 并处理"""

    insertSQL.runsql()

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    csv_paths = get_csv_paths()
    if not csv_paths:
        return

    unique_pending = check_pending()

    if unique_pending:
        print("\n🔔 发现待补全的默认分类备注，不生成 CSV，正在打开 UpdateDB 页面...")
        web_update_db.set_pending_names(unique_pending)
        web_update_db.run_server()
        return

    print("\n✅ 默认分类完整，开始生成 CSV 文件...")
    generate_csv()

if __name__ == "__main__":
    run()