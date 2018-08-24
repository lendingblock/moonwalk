from abc import ABC, abstractmethod


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


class BaseProxy(ABC):

    @classmethod
    @abstractmethod
    def validate_addr(cls, addr):
        pass

    @abstractmethod
    async def create_wallet(self):
        pass

    @abstractmethod
    async def send_money(self, priv, addrs):
        pass

    @abstractmethod
    async def get_balance(self, addr):
        pass
