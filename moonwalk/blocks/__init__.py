from .main import BaseBlock


def get(ccy: str) -> BaseBlock:
    return BaseBlock.BLOCKS[ccy]
