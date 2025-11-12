import py.app_saizon as app_saizon
import py.app_epos as app_epos
import py.app_paypay as app_paypay

def run():
    # SAIZON卡 账单输出事件
    app_saizon.main()
    
    # PAYPAY卡 账单输出事件
    app_paypay.main()

    # EPOS卡 账单输出事件
    app_epos.main()

if __name__ == "__main__":
    run()