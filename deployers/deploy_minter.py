from rift import *

from contracts.jetton_minter import JettonMinter
from contracts.jetton_wallet import JettonWallet


def deploy():
    init_data = JettonMinter.Data()
    init_data.admin = "EQCDRmpCsiy5fA0E1voWMpP-L4SQ2lX0liTk3zgFXcyLSYS3"
    init_data.total_supply = 10**11  # 100
    init_data.content = Cell()
    init_data.wallet_code = JettonWallet.code()
    msg, addr = JettonMinter.deploy(init_data, amount=2 * 10 ** 8)
    return msg, False
