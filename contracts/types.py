from rift import *


class OP:
    Transfer = 0xF8A7EA5
    TransferNotification = 0x7362D09C
    InternalTransfer = 0x178D4519
    Excesses = 0xD53276DB
    Burn = 0x595F07BC
    BurnNotification = 0x7BDD97DE


class MinterOP:
    MINT = 21
    CHANGE_ADMIN = 3
    CHANGE_CONTENT = 4


class TransferBody(Payload):
    query_id: uint64
    amount: Coin
    dest: MsgAddress
    response_dest: MsgAddress
    custom_payload: Maybe[Ref[Cell]]
    forward_ton: Coin
    forward_payload: Either[Cell, Ref[Cell]]


class InternalTransferBody(Payload):
    query_id: uint64
    amount: Coin
    from_: MsgAddress
    response_addr: MsgAddress
    forward_ton: Coin
    forward_payload: Either[Cell, Ref[Cell]]


class BurnBody(Payload):
    query_id: uint64
    amount: Coin
    response_dest: MsgAddress
    custom_payload: Maybe[Ref[Cell]]


class BurnNotification(Payload):
    op: uint32
    query_id: uint64
    amount: Coin
    owner: MsgAddress
    response: MsgAddress


class TransferNotification(Payload):
    op: uint32
    query_id: uint64
    amount: Coin
    from_: MsgAddress
    payload: Either[Cell, Ref[Cell]]


class Excess(Payload):
    op: uint32
    query_id: uint64


class MintMasterMessage(Payload):
    op: uint32
    body: InternalTransferBody


class MintBody(Payload):
    to: MsgAddress
    amount: Coin
    # Master Message
    master_msg: Ref[MintMasterMessage]
