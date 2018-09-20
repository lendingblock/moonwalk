class BlockBaseError(Exception):
    def __init__(self, data=None):
        self.data = data
        super().__init__()

    error = None


class EthereumError(BlockBaseError):
    error = 'unknown_error'


class ReplacementTransactionError(Exception):
    pass


class NotEnoughAmountError(BlockBaseError):
    error = 'not_enough_amount'
