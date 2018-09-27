from decimal import Decimal as D
from typing import Dict, Tuple, List

from moonwalk import utils
from moonwalk.blocks.eth import EthereumProxy
from moonwalk.blocks.ltc import LitecoinProxy
from moonwalk.blocks.lnd import LendingblockProxy
from moonwalk.blocks.bitcoin import BitcoinProxy
from moonwalk.blocks.bitcoin_cash import BitcoinCashProxy


class BlockError(Exception):
    pass


class WrongKeyError(BlockError):
    pass


class WrongAddressError(BlockError):
    pass


class InsufficientFoundsError(BlockError):
    pass


class BaseBlock:
    CCY: str = None
    BLOCKS: Dict[str, 'BaseBlock'] = {}

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


class Dummycoin(BaseBlock):
    """used in tests"""
    ADDRESSES = {}
    PRIV_KEYS = {}

    def validate_addr(self, addr):
        if addr in self.ADDRESSES:
            return addr

    async def create_wallet(self):
        addr = utils.rand_str()
        priv_key = f'1_{addr}'
        self.ADDRESSES[addr] = D(0)
        self.PRIV_KEYS[priv_key] = addr
        return addr, priv_key

    async def send_money(self, priv, addrs):
        for addr, amount in addrs:
            if not self.validate_addr(addr):
                raise WrongAddressError(addr)

        wallet_addr = priv[2:]
        balance = self.ADDRESSES[wallet_addr]

        sum_amounts = sum(addr[1] for addr in addrs)

        if balance < sum_amounts:
            raise InsufficientFoundsError(str(balance))

        self.ADDRESSES[wallet_addr] -= sum_amounts
        for addr, amount in addrs:
            self.ADDRESSES[addr] += amount

        return utils.rand_str()

    async def get_balance(self, addr):
        if addr not in self.ADDRESSES:
            raise WrongAddressError(addr)
        return self.ADDRESSES[addr]


class Bitcoin(BaseBlock):
    CCY = 'BTC'

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
    CCY = 'ETH'

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
    CCY = 'LTC'

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
    CCY = 'BCH'

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
    CCY = 'LND'

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
