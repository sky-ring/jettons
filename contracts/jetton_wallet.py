from rift import *

from .types import (
    OP,
    BurnBody,
    BurnNotification,
    Excess,
    InternalTransferBody,
    TransferBody,
    TransferNotification,
)
from .util import Utils

MIN_STORAGE_TONS = 10000000
GAS_CONSUMPTION = 10000000


class JettonWallet(Contract):
    """Jetton Wallet Contract."""

    class Data(Model):
        balance: Coin
        owner: MsgAddress
        master: MsgAddress
        wallet_code: Ref[Cell]

    data: Data

    def internal_receive(self) -> None:
        if self.body.is_empty():
            return
        message = self.message
        body = self.body
        if message.info.bounced:
            self.on_bounce(body)
            return
        sender = message.info.src
        fwd_fee = message.info.fwd_fee
        op = body >> uint32
        if op == OP.Transfer:
            self.send_tokens(body, sender, self.in_value, fwd_fee)
            return
        if op == OP.InternalTransfer:
            self.receive_tokens(
                body, sender, self.balance, fwd_fee, self.in_value
            )
            return
        if op == OP.Burn:
            self.burn_tokens(body, sender, self.in_value, fwd_fee)
            return
        raise 0xFFFF

    @method()
    def on_bounce(self, body: Slice):
        body.skip_n_(32)  # 0xFFFFFFFF
        op = body >> uint32
        assert (op == OP.BurnNotification) | (op == OP.InternalTransfer), 709
        body >> uint64
        amount = body >> Coin
        self.data.balance += amount
        self.data.save()

    @method()
    def send_tokens(
        self,
        body: TransferBody,
        sender: MsgAddress,
        value: int,
        fwd_fee: int,
    ):
        Utils.force_chain(body.dest)
        self.data.balance -= body.amount
        assert sender.is_equal(self.data.owner), 705
        assert self.data.balance >= 0, 706
        c = ContractDeployer[JettonWallet](
            code="wallet_code",
            owner=self.data.owner,
            master=self.data.master,
            balance=0,
            wallet_code=self.data.wallet_code,
        )
        msg_body = InternalTransferBody(
            op=OP.InternalTransfer,
            query_id=body.query_id,
            amount=body.amount,
            from_=self.data.owner,
            response_addr=body.response_dest,
            forward_ton=body.forward_ton,
            forward_payload=body.__data__,
        )
        msg = InternalMessage[InternalTransferBody].build(
            dest=c.address,
            amount=0,
            state_init=c.state_init,
            body=msg_body.as_ref(),
        )
        fwd_count = 1
        if body.forward_ton:
            fwd_count = 2
        assert value > (
            body.forward_ton
            + fwd_count * fwd_fee
            + (2 * GAS_CONSUMPTION + MIN_STORAGE_TONS)
        ), 709
        msg.send(MessageMode.CARRY_REM_VALUE)
        self.data.save()

    @method()
    def receive_tokens(
        self,
        body: InternalTransferBody,
        sender: MsgAddress,
        ton_balance: int,
        fwd_fee: int,
        value: int,
    ):
        self.data.balance += body.amount
        is_master = self.data.master.is_equal(sender)
        child_valid_addr = ContractDeployer[JettonWallet](
            code="wallet_code",
            owner=self.data.owner,
            master=self.data.master,
            balance=0,
            wallet_code=self.data.wallet_code,
        ).address
        is_child_wallet = sender.is_equal(child_valid_addr)
        assert is_master | is_child_wallet, 707
        fwd_amount = body.forward_ton
        ton_before = ton_balance - value
        storage_fee = MIN_STORAGE_TONS - std.min(ton_before, MIN_STORAGE_TONS)
        value = value - storage_fee + GAS_CONSUMPTION
        if fwd_amount:
            value = value - fwd_amount + fwd_fee
            notification = TransferNotification(
                op=OP.TransferNotification,
                amount=body.amount,
                query_id=body.query_id,
                from_=body.from_,
                payload=body.rest(),
            )
            msg = InternalMessage[TransferNotification].build(
                dest=self.data.owner,
                amount=fwd_amount,
                body=notification.as_ref(),
                bounce=0,
            )
            msg.send(MessageMode.ORDINARY, MessageFlag.FLAG_SEPERATE_FEE)
        if (body.response_addr.uint(2) != 0) & (value > 0):
            notification = Excess(
                op=OP.Excesses,
                query_id=body.query_id,
            )
            msg = InternalMessage[Excess].build(
                dest=body.response_addr,
                amount=value,
                body=notification.as_ref(),
                bounce=0,
            )
            msg.send(MessageMode.ORDINARY, MessageFlag.FLAG_IGNORE_ACTION_ERR)
        self.data.save()

    @method()
    def burn_tokens(
        self,
        body: BurnBody,
        sender: MsgAddress,
        value: int,
        fwd_fee: int,
    ):
        query_id = body.query_id
        self.data.balance -= body.amount
        assert self.data.owner.is_equal(sender), 705
        assert self.data.balance >= 0, 706
        assert value > fwd_fee + 2 * GAS_CONSUMPTION, 707

        mb = BurnNotification(
            op=OP.BurnNotification,
            query_id=query_id,
            amount=body.amount,
            owner=self.data.owner,
            response=body.response_dest,
        )
        msg = InternalMessage[BurnNotification].build(
            dest=self.data.master,
            body=mb.as_ref(),
        )
        msg.send(MessageMode.CARRY_REM_VALUE)
        self.data.save()
