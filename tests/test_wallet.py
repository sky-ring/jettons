from rift import *
from contracts.jetton_wallet import JettonWallet
from contracts.types import TransferBody, InternalTransferBody


def create_data(balance: int = 6, master: int = 1, owner: int = 2):
    data = JettonWallet.Data()
    data.master = MsgAddress.std(0, master)
    data.balance = int(balance * 10e9)
    data.owner = MsgAddress.std(0, owner)
    data.wallet_code = JettonWallet.code()
    return data


def create_transfer_body(
    query_id: int = 0,
    amount: int = 1e9,
    dest: int = 3,
    r_dest: int = 0,
    custom_payload=None,
    forward_ton: int = 0,
    forward_payload=None,
    wc: int = 0,
):
    body = TransferBody()
    body.query_id = query_id
    body.amount = int(amount)
    if dest == 0:
        dest = MsgAddress.empty()
    else:
        dest = MsgAddress.std(wc, dest)
    if r_dest == 0:
        r_dest = MsgAddress.empty()
    else:
        r_dest = MsgAddress.std(wc, r_dest)
    body.dest = dest
    body.response_dest = r_dest
    body.custom_payload = custom_payload
    body.forward_ton = forward_ton
    body.forward_payload = forward_payload
    return body


def test_transfer():
    data = create_data().as_cell()
    wallet = JettonWallet.instantiate(data)
    body = create_transfer_body(dest=3, amount=1234)
    res = wallet.send_tokens(
        body.as_cell().parse(), MsgAddress.std(0, 2), int(10e9), 0,
    )
    res.expect_ok()
    actions = res.actions()
    assert len(actions) == 1
    msg = actions[0]
    assert msg["type"] == "send_msg"
    assert msg["mode"] == 64

    message = InternalMessage[InternalTransferBody](msg["message"].parse())
    assert message.body.amount == 1234


def test_transfer_no_value():
    data = create_data().as_cell()
    wallet = JettonWallet.instantiate(data)
    body = create_transfer_body(dest=3)
    res = wallet.send_tokens(
        body.as_cell().parse(), MsgAddress.std(0, 2), 0, 0,
    )
    res.expect_error()


def test_transfer_not_owner():
    data = create_data().as_cell()
    wallet = JettonWallet.instantiate(data)
    body = create_transfer_body(dest=3)
    res = wallet.send_tokens(
        body.as_cell().parse(), MsgAddress.std(0, 3), int(10e9), 0,
    )
    res.expect_error()


def test_transfer_other_chain():
    data = create_data().as_cell()
    wallet = JettonWallet.instantiate(data)
    body = create_transfer_body(dest=3, wc=1)
    res = wallet.send_tokens(
        body.as_cell().parse(), MsgAddress.std(0, 2), int(10e9), 0,
    )
    res.expect_error()
