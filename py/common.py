import csv,re,unicodedata

DEFAULT_CAT = "默认"
_RE_ZEN_NUM = r"[０-９]+"

def open_csv_with_guess(path):
    # 兼容 UTF-8/BOM 与 Shift_JIS
    for enc in ("utf-8-sig", "shift_jis"):
        try:
            f = open(path, newline="", encoding=enc)
            # 先试读一行验证列名是否可解析
            pos = f.tell()
            reader = csv.DictReader(f)
            if reader.fieldnames and len(reader.fieldnames) >= 3:
                f.seek(pos)
                return f, reader
            f.close()
        except Exception:
            pass
    # 回退：用utf-8-sig再开一次让错误抛出
    return open(path, newline="", encoding="utf-8-sig"), csv.DictReader(open(path, newline="", encoding="utf-8-sig"))

# 分类, 二级分类
def lookup_category(conn, merchant_name: str):
    row = conn.execute(
        "SELECT type1, type2 FROM merchant_catalog WHERE name=?",
        (merchant_name,)
    ).fetchone()
    if row:
        return row[0], row[1]  
    return DEFAULT_CAT, ""     # 未匹配的默认规则

# 校验必需列
def ensure_columns(reader, need_cols):
    missing = [c for c in need_cols if c not in (reader.fieldnames or [])]
    if missing:
        raise KeyError(f"输入CSV缺少列: {missing}，当前列名: {reader.fieldnames}")

# 只做“是否属于这四类”的模糊判断；命中时返回规范关键词，用它去数据库查
def fuzzy_pick(merchant_raw: str) -> str | None:
    s = unicodedata.normalize("NFKC", merchant_raw or "")
    # 连字符与空白统一，提升容错（仅用于判断，不改你数据库/输出）
    s = s.replace("-", "ー").replace("‐", "ー")
    s = re.sub(r"\s+", "", s)
    patterns = [
        (r"ロ.?ーソン",              "ロ-ソン"),           # Lawson
        (r"セブン.?イレブン",        "セブン-イレブン"),    # 7-Eleven
        (r"(?:ファ|フア)ミリ.?マ.?ト","フアミリ―マ―ト"),    # FamilyMart（兼容ファ/フア、中点/连字符）
        (r"ドコモ.*ご利用料金",       "ドコモご利用料金"),  # docomo usage charge
    ]
    for pat, canon in patterns:
        if re.search(pat, s, flags=re.IGNORECASE):
            return canon
    return None

# app_paypay.py专用
def strip_paypay_prefix(name: str) -> str:
    if not name:
        return ""

    s = name.lstrip()  # 只去掉左侧空白，不做 NFKC，不影响中间格式

    # PayPay 前缀的多写法（不做 normalize）
    # 覆盖：
    # ＰａｙＰａｙ / ＰＡＹＰＡＹ / PayPay / PAYPAY / paypay
    # 以及中间带空格的：Ｐａｙ Ｐａｙ / Pay Pay / pay pay
    prefix_pattern = (
        r"^(?:"
        r"ＰａｙＰａｙ|ＰＡＹＰＡＹ|PayPay|PAYPAY|paypay|"
        r"Ｐａｙ\s*Ｐａｙ|Pay\s*Pay|pay\s*pay"
        r")"
    )

    # 前缀后可能跟的分隔符（包含全角空格 \u3000）
    sep_pattern = r"[\u3000\s·･・ー\-—–~：:、／/・,，。．｡]*"

    s = re.sub(prefix_pattern + sep_pattern, "", s, flags=re.IGNORECASE)

    return s.strip()  # 只去除首尾空白，中间不动

# app_paypay.py专用
# 规则：若是「全角数字+月分家賃/保証料」，则仅保留「月分家賃/月分保証料」作为查库键
def normalize_for_lookup(s: str) -> str:
    s = s or ""
    # 保持原样（不做NFKC）以便识别全角数字模式
    if re.fullmatch(_RE_ZEN_NUM + r"月分家賃", s):
        return "月分家賃"
    if re.fullmatch(_RE_ZEN_NUM + r"月分保証料", s):
        return "月分保証料"
    return s



def normalize_date(date_str: str) -> str:
    """
    把各种类似：
        2025年1月5日
        2025/01/05
        2025-1-5
        2025.1.5
    统一转换成：20250105（YYYYMMDD）
    """
    if not date_str:
        return ""

    s = date_str.strip()

    # 抓出 年、月、日
    m = re.match(r'^(\d{4})\D+(\d{1,2})\D+(\d{1,2})', s)
    if not m:
        return s  # 不符合日期格式就原样返回

    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))

    return f"{year:04d}{month:02d}{day:02d}"