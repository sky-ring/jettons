from dbuilder import *

WORKCHAIN = 0


class Utils(Library):
    @method(static=True)
    def force_chain(ctx, addr: Slice):
        wc, _ = addr.parse_std_addr()
        assert wc == WORKCHAIN, 333