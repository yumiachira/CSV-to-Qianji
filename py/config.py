# DB固定值
DB_PATH = "./db/ledger.db"
CSV_FILE = "./db/table.csv" # 你的CSV：name,type1,type2（UTF-8 或 UTF-8 BOM皆可）
CSV_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS merchant_catalog (
  name  TEXT PRIMARY KEY,  -- 商户名（原样）
  type1 TEXT NOT NULL,     -- 分类1
  type2 TEXT NOT NULL      -- 分类2
);
"""

# 输出CSV表头与固定值
OUT_HEADERS = ["时间","分类","二级分类","类型","金额","账户1","账户2","备注","账单标记","手续费","优惠券","标签","账单图片"]
FIX_TYPE    = "支出"
DEFAULT_CAT = "默认"

# SAIZON卡账单格式
SAIZON_COL_DATE    = "利用日"
SAIZON_COL_MERCHANT= "ご利用店名及び商品名"
SAIZON_COL_AMOUNT  = "利用金額"
SAIZON_COL_NOTE    = "備考"
SAIZON_FIX_ACCOUNT = "SAIZONクレジット"   # 固定账户名称

# PAYPAY卡账单格式
PAYPAY_COL_DATE      = "利用日/キャンセル日"
PAYPAY_COL_MERCHANT  = "利用店名・商品名"
PAYPAY_COL_PAYTYPE   = "支払区分"
PAYPAY_COL_AMOUNT    = "利用金額"
PAYPAY_FIX_ACCOUNT   = "PAYPAY" # 固定账户名称

# EPOS卡账单格式
EPOS_COL_TYPE        = "種別（ショッピング、キャッシング、その他）"
EPOS_COL_DATE        = "ご利用年月日"
EPOS_COL_PLACE       = "ご利用場所"
EPOS_COL_CONTENT     = "ご利用内容"
EPOS_COL_AMOUNT      = "ご利用金額（キャッシングでは元金になります）"
EPOS_COL_PAY_KBN     = "支払区分"
EPOS_COL_START_MONTH = "お支払開始月"
EPOS_COL_NOTE        = "備考"
EPOS_FIX_ACCOUNT     = "EPOS" # 固定账户名称