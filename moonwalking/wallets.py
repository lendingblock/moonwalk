from .main import BLOCKS


def block(currency):
    block = BLOCKS.get(currency)
    if not block:
        raise ValueError(f'Blockchain {currency} not supported')
    return block


def validate_addr(currency, addr):
    return block(currency).validate_addr(addr)


def create_addr(currency):
    return block(currency).create_addr()


async def create_wallet(currency):
    return await block(currency).create_wallet()
