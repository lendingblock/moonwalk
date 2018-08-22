from decimal import Decimal as D
from typing import Dict, Tuple, List

from lbcore.db.order_values import Ccy

from .eth import EthereumProxy
from .ltc import LitecoinProxy
from .lnd import LendingblockProxy
from .bitcoin import BitcoinProxy
from .bitcoin_cash import BitcoinCashProxy


class BlockError(Exception):
    pass


class WrongKeyError(BlockError):
    pass


class WrongAddressError(BlockError):
    pass


class InsufficientFoundsError(BlockError):
    pass


class BaseBlock:
    CCY: Ccy = None
    BLOCKS: Dict[Ccy, 'BaseBlock'] = {}

    def __init_subclass__(cls, **kwargs):
        if cls.CCY in BaseBlock.BLOCKS:
            raise ValueError(f"Block already there for {cls.CCY}")
        if cls.CCY:
            BaseBlock.BLOCKS[cls.CCY] = cls()
        super().__init_subclass__(**kwargs)

    def validate_addr(self, addr: str):
        raise NotImplementedError

    async def create_wallet(self) -> Tuple[str, str]:
        raise NotImplementedError

    async def send_money(self, priv: str, addrs: List[Tuple[str, D]]) -> str:
        raise NotImplementedError

    async def get_balance(self, addr: str) -> D:
        raise NotImplementedError


class Bitcoin(BaseBlock):
    CCY = Ccy.BTC

    def __init__(self):
        self.proxy = BitcoinProxy()

    def validate_addr(self, addr):
        return self.proxy.validate_addr(addr)

    async def send_money(self, priv, addrs):
        return await self.proxy.send_money(priv, addrs)

    async def get_balance(self, addr):
        return await self.proxy.get_balance(addr)

    async def create_wallet(self):
        return await self.proxy.create_wallet()


class Ethereum(BaseBlock):
    CCY = Ccy.ETH

    def __init__(self):
        self.proxy = EthereumProxy()

    def validate_addr(self, addr: str):
        return self.proxy.validate_addr(addr)

    async def send_money(self, priv, addrs):
        return await self.proxy.send_money(priv, addrs)

    async def get_balance(self, addr):
        return await self.proxy.get_balance(addr)

    async def create_wallet(self):
        return self.proxy.create_wallet()


class Litecoin(BaseBlock):
    CCY = Ccy.LTC

    def __init__(self):
        self.proxy = LitecoinProxy()

    def validate_addr(self, addr):
        return self.proxy.validate_addr(addr)

    async def send_money(self, priv, addrs):
        return await self.proxy.send_money(priv, addrs)

    async def get_balance(self, addr):
        return await self.proxy.get_balance(addr)

    async def create_wallet(self):
        return await self.proxy.create_wallet()


class BitcoinCash(BaseBlock):
    CCY = Ccy.BCH

    def __init__(self):
        self.proxy = BitcoinCashProxy()

    def validate_addr(self, addr):
        return self.proxy.validate_addr(addr)

    async def send_money(self, priv, addrs):
        return await self.proxy.send_money(priv, addrs)

    async def get_balance(self, addr):
        return await self.proxy.get_balance(addr)

    async def create_wallet(self):
        return await self.proxy.create_wallet()


class Lendingblock(BaseBlock):
    CCY = Ccy.LND

    def __init__(self):
        self.proxy = LendingblockProxy()

    def validate_addr(self, addr):
        return self.proxy.validate_addr(addr)

    async def send_money(self, priv, addrs):
        return await self.proxy.send_money(priv, addrs)

    async def get_balance(self, addr):
        return await self.proxy.get_lnd_balance(addr)

    async def create_wallet(self):
        return await self.proxy.create_wallet()
