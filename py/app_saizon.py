# export_saizon.py
import csv, sqlite3, os
from py.common import (
    open_csv_with_guess,
    lookup_category,
    ensure_columns,
    fuzzy_pick
    )
from py.config import (
    DB_PATH,
    OUT_HEADERS,
    FIX_TYPE,
    PAY_TYPE,
    CAT_REFUND,
    DEFAULT_CAT
    )
from py.config import (
    SAIZON_COL_DATE,
    SAIZON_COL_MERCHANT,
    SAIZON_COL_AMOUNT,
    SAIZON_COL_NOTE,
    SAIZON_FIX_ACCOUNT
    )

def outputCSV(csv_file,output_csvname):

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"未找到数据库文件: {os.path.abspath(DB_PATH)}")

    conn = sqlite3.connect(DB_PATH)

    f_in, reader = open_csv_with_guess(csv_file)

    # 校验必需列
    need_cols = [SAIZON_COL_DATE, SAIZON_COL_MERCHANT, SAIZON_COL_AMOUNT, SAIZON_COL_NOTE]
    ensure_columns(reader, need_cols)

    with f_in, open(output_csvname, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=OUT_HEADERS)
        writer.writeheader()

        for row in reader:  # DictReader 自动从第二行开始
            date_val = (row.get(SAIZON_COL_DATE) or "").strip()
            merchant = (row.get(SAIZON_COL_MERCHANT) or "").strip()
            amount   = (row.get(SAIZON_COL_AMOUNT) or "").strip()
            note_val = (row.get(SAIZON_COL_NOTE) or "").strip()
            # 跳过 CSV 表头
            if date_val == SAIZON_COL_DATE:
                continue

            # 备注 = 商户 + 備考（如果有）
            if note_val:
                remark = f"{merchant} {note_val}"
            else:
                remark = merchant

            # 先判断是否属于四个“模糊匹配”关键词之一
            alias = fuzzy_pick(merchant)
            if alias:
                # 命中四类之一 → 仅用规范关键词去库里查（不再用原始商户名）
                hit = lookup_category(conn, alias)
                if hit:
                    cat, subcat = hit
                else:
                    cat, subcat = DEFAULT_CAT, ""
            else:
                # 不属于四类 → 按原始商户名精确查
                hit = lookup_category(conn, merchant)
                if hit:
                    cat, subcat = hit
                else:
                    cat, subcat = DEFAULT_CAT, ""
                    
            # 注意：SAIZON卡账单没有收入，金额为负数时视为退款
            if amount<"0":
                trans_type = PAY_TYPE
                cat = CAT_REFUND  # 退款类交易强制分类为「退款」
                subcat = ""
            else:
                trans_type = FIX_TYPE

            out_row = {
                "时间": date_val,
                "分类": cat,
                "二级分类": subcat,
                "类型": trans_type,
                "金额": amount,
                "账户1": SAIZON_FIX_ACCOUNT,
                "账户2": "",
                "备注": remark,
                "账单标记": "",
                "手续费": "",
                "优惠券": "",
                "标签": "",
                "账单图片": ""
            }
            writer.writerow(out_row)

    conn.close()
    print(f"🔸 已生成: {os.path.abspath(output_csvname)}")