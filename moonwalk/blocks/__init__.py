from lbcore.db.order_values import Ccy

from .main import BaseBlock


def get(ccy: Ccy) -> BaseBlock:
    return BaseBlock.BLOCKS[ccy]
