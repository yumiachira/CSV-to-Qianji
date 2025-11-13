💳 日本信用卡账单自动转换工具

将日本主要信用卡（セゾンカード、EPOSカード、PAYPAYカード）的账单 CSV

自动转换为 钱迹App 的标准导入格式。


🚀 功能说明

1.支持三种信用卡账单格式：

 ·セゾンカード（Saison Card）
 
 ·EPOSカード（Epos Card）
 
 ·PAYPAYカード（PayPay Card）
 
2.自动标准化账单格式，生成可直接导入钱迹App的 CSV 文件

3.支持自定义分类、商户归属（如 711、ローソン 自动识别为“超市”）

4.SQLite 数据库持久化记录，可手动扩展分类规则



📂 目录结构

app/

 ├── input/          # 放置原始账单CSV文件
 
 ├── output/         # 自动生成的钱迹标准账单文件
 
 ├── db/
 
 │    ├── ledger.db  # 程序运行时使用的数据库（自动生成）
 
 │    └── table.csv  # 自定义分类数据源
 
 ├── py/
 
 │    ├── app_saizon.py   # 处理セゾン卡
 
 │    ├── app_epos.py     # 处理EPOS卡
 
 │    ├── app_paypay.py   # 处理PAYPAY卡
 
 │    ├── config.py       # 配置项
 
 │    ├── common.py       # 公共函数
 
 │    ├── insertSQL.py    # 初始化数据库
 
 │    └── set_name.py     # 输入输出文件名配置
 
 └── main.py         # 主程序入口
 


🧩 使用方法

（1）放置账单文件

将下载好的信用卡账单 CSV 放入：app/input/

※文件名可任意，程序会自动识别账单类型（Saison / EPOS / PayPay）,支持一次放多个 CSV 批量转换

（2） 运行程序

 执行：python main.py

（3) 查看输出

 转换后的账单会自动生成在：app/output/
 
 ※输出文件名格式为 【output_{账单类型}_{起始日期}-{结束日期}.csv】


⚠️ 注意事项
 如果想修改分类规则：
 
 编辑自定义文件：db/table.csv 即可
 

🛠️ 环境要求

Python 3.8 及以上（推荐 3.10+）

依赖模块：

 -csv
 
 -sqlite3
 
 -os
 
 -re
 
 -unicodedata

 

📄 许可证

本项目仅用于学习与个人财务管理用途，

请勿用于商业或非法用途。



💬 作者

Cola箘

