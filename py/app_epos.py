# export_saizon.py
import csv, sqlite3, os
from py.common import (
    open_csv_with_guess,
    lookup_category,
    ensure_columns,
    fuzzy_pick,
    normalize_for_lookup
    )
from py.config import (
    DB_PATH,
    OUT_HEADERS,
    FIX_TYPE,
    DEFAULT_CAT
    )
from py.config import (
    EPOS_COL_TYPE,
    EPOS_COL_DATE,
    EPOS_COL_PLACE,
    EPOS_COL_CONTENT,
    EPOS_COL_AMOUNT,
    EPOS_COL_PAY_KBN,
    EPOS_COL_START_MONTH,
    EPOS_COL_NOTE,
    EPOS_FIX_ACCOUNT
    )

def outputCSV(csv_file,output_csvname):

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"未找到数据库文件: {os.path.abspath(DB_PATH)}")

    conn = sqlite3.connect(DB_PATH)
    f_in, reader = open_csv_with_guess(csv_file)

    # 校验必需列
    need_cols = [EPOS_COL_TYPE, EPOS_COL_DATE, EPOS_COL_PLACE, EPOS_COL_CONTENT, EPOS_COL_AMOUNT, EPOS_COL_PAY_KBN, EPOS_COL_START_MONTH, EPOS_COL_NOTE]
    ensure_columns(reader, need_cols)

    with f_in, open(output_csvname, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=OUT_HEADERS)
        writer.writeheader()

        for row in reader:
            type_val   = (row.get(EPOS_COL_TYPE) or "").strip()
            date_val   = (row.get(EPOS_COL_DATE) or "").strip()
            place_val  = (row.get(EPOS_COL_PLACE) or "").strip()
            cont_val   = (row.get(EPOS_COL_CONTENT) or "").strip()
            amount     = (row.get(EPOS_COL_AMOUNT) or "").strip()
            pay_kbn    = (row.get(EPOS_COL_PAY_KBN) or "").strip()
            note_val   = (row.get(EPOS_COL_NOTE) or "").strip()
            
            if type_val == EPOS_COL_TYPE:
                continue

            # —— 输出字段映射 —— #
            out_time   = date_val
            out_amount = amount
            out_acct1  = f"{EPOS_FIX_ACCOUNT}{pay_kbn}"  # 拼接「EOPS + 支払区分」
            out_acct2  = ""

            # 备注与“查库键”的选择：
            # ・ショッピング → 备注=ご利用場所
            # ・その他ご利用 → 备注=ご利用内容
            # ・其他类型（如キャッシング等）→ 尝试优先ご利用場所，否则ご利用内容，否则備考
            if type_val == "ショッピング":
                remark = place_val
            elif type_val == "その他ご利用":
                remark = cont_val
            else:
                remark = place_val or cont_val or note_val

            # 根据规则4对查库键做特殊归一
            lookup_key = normalize_for_lookup(remark)

            alias = fuzzy_pick(lookup_key)
            if alias:
                hit = lookup_category(conn, alias)
                if hit:
                    cat, subcat = hit
                else:
                    cat, subcat = DEFAULT_CAT, ""
            else:
                hit = lookup_category(conn, lookup_key)
                if hit:
                    cat, subcat = hit
                else:
                    cat, subcat = DEFAULT_CAT, ""

            out_row = {
                "时间": out_time,
                "分类": cat,
                "二级分类": subcat,
                "类型": FIX_TYPE,
                "金额": out_amount,
                "账户1": out_acct1,
                "账户2": out_acct2,
                "备注": remark,        # 按需求：备注只放设定值
                "账单标记": "",
                "手续费": "",
                "优惠券": "",
                "标签": "",
                "账单图片": ""
            }
            writer.writerow(out_row)

    conn.close()
    print(f"🔸 已生成: {os.path.abspath(output_csvname)}")
