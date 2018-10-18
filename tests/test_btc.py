from decimal import Decimal as D

import pytest
from bitcoin.core import COIN

from moonwalking.main import Bitcoin
from moonwalking.blocks.exc import NotEnoughAmountError


async def test_basic_bitcoin_ops(fee_mocker):
    bitcoin = Bitcoin()
    addr1, priv1 = await bitcoin.create_wallet()
    addr2, priv2 = await bitcoin.create_wallet()
    addr3, priv3 = await bitcoin.create_wallet()

    assert bitcoin.validate_addr(addr1)
    assert bitcoin.validate_addr(addr2)
    assert bitcoin.validate_addr(addr3)

    await bitcoin.post('sendtoaddress', addr1, 20000 / COIN)
    await bitcoin.post('generate', 1)
    assert await bitcoin.get_balance(addr1) == D(20000) / COIN

    tx_id = await bitcoin.send_money(
        priv1,
        [(addr2, D(5000) / COIN), (addr3, D(15000) / COIN)]
    )
    assert tx_id
    await bitcoin.post('generate', 1)

    # 500 fee splited equally onto 2 recievers:
    assert (await bitcoin.get_balance(addr1)) == D(0)
    assert (await bitcoin.get_balance(addr2)) == D(5000 - 250) / COIN
    assert (await bitcoin.get_balance(addr3)) == D(15000 - 250) / COIN


async def test_new_wallet_empty():
    bitcoin = Bitcoin()
    addr1, priv1 = await bitcoin.create_wallet()
    assert bitcoin.validate_addr(addr1)
    assert (await bitcoin.get_balance(addr1)) == D(0)


async def test_insufficient_amount(fee_mocker):
    bitcoin = Bitcoin()
    addr1, priv1 = await bitcoin.create_wallet()
    addr2, priv2 = await bitcoin.create_wallet()
    assert bitcoin.validate_addr(addr1)
    await bitcoin.post('sendtoaddress', addr1, 10000 / COIN)
    with pytest.raises(NotEnoughAmountError):
        await bitcoin.send_money(priv1, [(addr2, D(15000) / COIN)])


async def test_insufficient_amount_to_cover_fee(fee_mocker):
    bitcoin = Bitcoin()
    addr1, priv1 = await bitcoin.create_wallet()
    addr2, priv2 = await bitcoin.create_wallet()
    assert bitcoin.validate_addr(addr1)
    await bitcoin.post('sendtoaddress', addr1, 10000 / COIN)
    with pytest.raises(NotEnoughAmountError):
        await bitcoin.send_money(priv1, [(addr2, D(10001) / COIN)])
