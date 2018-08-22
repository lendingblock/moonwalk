from abc import ABC, abstractmethod
from decimal import Decimal as D
from typing import Dict, Tuple, List

from .bitcoin import BitcoinProxy
from .bitcoin_cash import BitcoinCashProxy
from .eth import EthereumProxy
from .lnd import LendingblockProxy
from .ltc import LitecoinProxy


class BaseBlock(ABC):
    symbol = None
    BLOCKS: Dict[str, 'BaseBlock'] = {}

    def __init_subclass__(cls, **kwargs):
        if cls.symbol in BaseBlock.BLOCKS:
            raise ValueError(f"Block already there for {cls.CCY}")
        if cls.symbol:
            BaseBlock.BLOCKS[cls.symbol] = cls()
        super().__init_subclass__(**kwargs)

    @abstractmethod
    def validate_addr(self, addr: str):
        pass

    @abstractmethod
    async def create_wallet(self) -> Tuple[str, str]:
        pass

    @abstractmethod
    async def send_money(self, priv: str, addrs: List[Tuple[str, D]]) -> str:
        pass

    @abstractmethod
    async def get_balance(self, addr: str) -> D:
        pass


class Bitcoin(BaseBlock):
    symbol = 'BTC'

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
    symbol = 'ETH'

    def __init__(self):
        self.proxy = EthereumProxy()

    def validate_addr(self, addr: str):
        return self.proxy.validate_addr(addr)

    async def send_money(self, priv, addrs):
        return await self.proxy.send_money(priv, addrs)

    async def get_balance(self, addr):
        return await self.proxy.get_balance(addr)

    async def create_wallet(self):
        return await self.proxy.create_wallet()


class Litecoin(BaseBlock):
    symbol = 'LTC'

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
    symbol = 'BCH'

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
    symbol = 'LND'

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
