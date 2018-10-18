from abc import ABC, abstractmethod
from decimal import Decimal as D
from typing import Dict, Tuple, List


class BlockBaseError(Exception):
    error = None

    def __init__(self, data=None):
        self.data = data
        super().__init__()


class EthereumError(BlockBaseError):
    error = 'unknown_error'


class ReplacementTransactionError(Exception):
    pass


class NotEnoughAmountError(BlockBaseError):
    error = 'not_enough_amount'


class BaseBlock(ABC):
    CCY: str = None
    BLOCKS: Dict[str, 'BaseBlock'] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.register()

    @classmethod
    def register(cls):
        if cls.CCY in BaseBlock.BLOCKS:
            raise ValueError(f"Block already there for {cls.CCY}")
        if cls.CCY:
            BaseBlock.BLOCKS[cls.CCY] = cls()

    @abstractmethod
    def validate_addr(self, addr: str):
        raise NotImplementedError

    @abstractmethod
    async def create_addr(self) -> Tuple[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def create_wallet(self) -> Tuple[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def send_money(self, priv: str, addrs: List[Tuple[str, D]]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_balance(self, addr: str) -> D:
        raise NotImplementedError
