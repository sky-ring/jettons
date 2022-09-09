from dbuilder import *

from .jetton_wallet import JettonWallet
from .types import (
    OP,
    BurnNotification,
    Excess,
    InternalTransferBody,
    MintBody,
    MinterOP,
)


class JettonMinter(Contract):
    """Jetton Wallet Contract."""

    class Data(Model):
        total_supply: Coin
        admin: MsgAddress
        content: Ref[Cell]
        wallet_code: Ref[Cell]

    data: Data

    def internal_receive(
        ctx,
        balance: int,
        msg_value: int,
        in_msg_full: Cell,
        in_msg_body: Slice,
    ) -> None:
        # what we'd look like to see
        if in_msg_body.is_empty():
            return
        m = InternalMessage(in_msg_full.parse())
        body = in_msg_body
        if m.info.bounced:
            # ignore bounced
            return
        sender = m.info.src
        op = body >> uint32
        if op == MinterOP.MINT:
            assert sender.is_equal(ctx.data.admin), 73
            b = MintBody(body)
            cd = ContractDeployer[JettonWallet](
                code="wallet_code",
                owner=b.to,
                master=std.my_address(),
                balance=0,
                wallet_code=ctx.data.wallet_code,
            )
            ctx.data.total_supply += b.master_msg.body.amount
            msg = InternalMessage[InternalTransferBody].build(
                dest=cd.address,
                amount=0,
                state_init=cd.state_init,
                body=b.master_msg.origin_slice(),
            )
            msg.send(MessageMode.ORDINARY, MessageFlag.FLAG_SEPERATE_FEE)
            ctx.data.save()
            return
        if op == OP.BurnNotification:
            b = BurnNotification(body)
            c = ContractDeployer[JettonWallet](
                code="wallet_code",
                owner=b.owner,
                master=std.my_address(),
                balance=0,
                wallet_code=ctx.data.wallet_code,
            )
            assert c.address.is_equal(sender), 74
            ctx.data.total_supply -= b.amount
            resp_addr = b.response
            if resp_addr.int(2) != 0:
                notification = Excess(
                    op=OP.Excesses,
                    query_id=b.query_id,
                )
                msg = InternalMessage[Excess].build(
                    dest=resp_addr,
                    amount=0,
                    body=notification,
                    bounce=0,
                )
                msg.send(
                    MessageMode.CARRY_REM_VALUE,
                    MessageFlag.FLAG_IGNORE_ACTION_ERR,
                )
            return
        if op == MinterOP.CHANGE_ADMIN:
            assert sender.is_equal(ctx.data.admin), 73
            ctx.data.admin = body >> MsgAddress
            ctx.data.save()
            return
        if op == MinterOP.CHANGE_CONTENT:
            assert sender.is_equal(ctx.data.admin), 73
            ctx.data.content = body >> Ref[Cell]
            ctx.data.save()
            return

        raise 0xFFFF
