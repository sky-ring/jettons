from rift import *

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

    def internal_receive(self) -> None:
        if self.body.is_empty():
            return
        if self.message.info.bounced:
            # ignore bounced
            return
        sender = self.message.info.src
        op = self.body >> uint32
        if op == MinterOP.MINT:
            assert sender.is_equal(self.data.admin), 73
            b = self.body % MintBody
            cd = ContractDeployer[JettonWallet](
                code="wallet_code",
                owner=b.to,
                master=std.my_address(),
                balance=0,
                wallet_code=self.data.wallet_code,
            )
            self.data.total_supply += b.master_msg.body.amount
            msg = InternalMessage[InternalTransferBody].build(
                dest=cd.address,
                amount=0,
                state_init=cd.state_init,
                body=b.master_msg.origin_slice(),
            )
            msg.send(MessageMode.ORDINARY, MessageFlag.FLAG_SEPERATE_FEE)
            self.data.save()
            return
        if op == OP.BurnNotification:
            b = self.body % BurnNotification
            c = ContractDeployer[JettonWallet](
                code="wallet_code",
                owner=b.owner,
                master=std.my_address(),
                balance=0,
                wallet_code=self.data.wallet_code,
            )
            assert c.address.is_equal(sender), 74
            self.data.total_supply -= b.amount
            resp_addr = b.response
            if resp_addr.sint(2) != 0:
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
            assert sender.is_equal(self.data.admin), 73
            self.data.admin = self.body >> MsgAddress
            self.data.save()
            return
        if op == MinterOP.CHANGE_CONTENT:
            assert sender.is_equal(self.data.admin), 73
            self.data.content = self.body >> Ref[Cell]
            self.data.save()
            return

        raise 0xFFFF
