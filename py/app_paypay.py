# export_saizon.py
import csv, sqlite3, os
from py.common import open_csv_with_guess,lookup_category,ensure_columns,fuzzy_pick,strip_paypay_prefix
from py.config import DB_PATH,OUT_HEADERS,FIX_TYPE,DEFAULT_CAT
from py.config import PAYPAY_COL_DATE,PAYPAY_COL_MERCHANT,PAYPAY_COL_PAYTYPE,PAYPAY_COL_AMOUNT,PAYPAY_FIX_ACCOUNT
from py.set_name import PAYPAY_INPUT_CSV,PAYPAY_OUTPUT_CSV

def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"未找到数据库文件: {os.path.abspath(DB_PATH)}")
    conn = sqlite3.connect(DB_PATH)

    f_in, reader = open_csv_with_guess(PAYPAY_INPUT_CSV)
    need_cols = [PAYPAY_COL_DATE, PAYPAY_COL_MERCHANT, PAYPAY_COL_PAYTYPE, PAYPAY_COL_AMOUNT]
    ensure_columns(reader, need_cols)

    with f_in, open(PAYPAY_OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=OUT_HEADERS)
        writer.writeheader()

        for row in reader:
            # 读取原值
            date_val   = (row.get(PAYPAY_COL_DATE) or "").strip()
            merchant   = (row.get(PAYPAY_COL_MERCHANT) or "").strip()
            paytype    = (row.get(PAYPAY_COL_PAYTYPE) or "").strip()
            amount     = (row.get(PAYPAY_COL_AMOUNT) or "").strip()

            # 跳过可能残留的表头行
            if date_val == PAYPAY_COL_DATE:
                continue

            # 输出需要的固定/映射字段
            out_time   = date_val
            out_type   = FIX_TYPE
            out_amount = amount
            out_acc1   = f"{PAYPAY_FIX_ACCOUNT}{paytype}".strip()  # 账户1 = "PAYPAY" + 支払区分
            out_remark = merchant                     # 备注 = 原始「利用店名・商品名」

            # —— 分类前处理：先去 PayPay 前缀
            merchant_key = strip_paypay_prefix(merchant)
            #Debug print(f"[DEBUG] 原商户: {merchant}  →  清洗后用于匹配: {merchant_key}")

            # —— 先试四类模糊；命中则用规范词去查库；否则用清洗后的原名查库
            alias = fuzzy_pick(merchant_key)
            if alias:
                hit = lookup_category(conn, alias)
                if hit:
                    cat, subcat = hit
                else:
                    cat, subcat = DEFAULT_CAT, ""
            else:
                hit = lookup_category(conn, merchant_key)
                if hit:
                    cat, subcat = hit
                else:
                    cat, subcat = DEFAULT_CAT, ""

            out_row = {
                "时间": out_time,
                "分类": cat,
                "二级分类": subcat,
                "类型": out_type,
                "金额": out_amount,
                "账户1": out_acc1,
                "账户2": "",
                "备注": out_remark,
                "账单标记": "",
                "手续费": "",
                "优惠券": "",
                "标签": "",
                "账单图片": ""
            }
            writer.writerow(out_row)

    conn.close()
    print(f"✅ 已生成: {os.path.abspath(PAYPAY_OUTPUT_CSV)}")