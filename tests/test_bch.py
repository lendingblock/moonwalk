from decimal import Decimal as D

import pytest
from bitcoin.core import COIN
from cashaddress.convert import to_cash_address

from moonwalking.main import BitcoinCash
from moonwalking.blocks.exc import NotEnoughAmountError


async def test_basic_bitcoin_cash_ops(fee_mocker):
    bitcoin_cash = BitcoinCash()
    addr1, priv1 = await bitcoin_cash.create_wallet()
    addr2, priv2 = await bitcoin_cash.create_wallet()
    addr3, priv3 = await bitcoin_cash.create_wallet()

    assert bitcoin_cash.validate_addr(addr1)
    assert bitcoin_cash.validate_addr(addr2)
    assert bitcoin_cash.validate_addr(addr3)

    await bitcoin_cash.post('sendtoaddress', addr1, 10000 / COIN)
    await bitcoin_cash.post('generate', 1)
    assert (await bitcoin_cash.get_balance(addr1)) == D(10000) / COIN
    assert (await bitcoin_cash.get_balance(
        to_cash_address(addr1)
    )) == D(10000) / COIN

    tx_id = await bitcoin_cash.send_money(
        priv1,
        [(addr2, D(500) / COIN), (to_cash_address(addr3), D(1500) / COIN)]
    )
    assert tx_id

    await bitcoin_cash.post('generate', 1)
    # 500 fee splited equally onto 2 recievers:
    assert (await bitcoin_cash.get_balance(addr1)) == D(10000 - 2000) / COIN
    assert (await bitcoin_cash.get_balance(addr2)) == D(500 - 250) / COIN
    assert (await bitcoin_cash.get_balance(addr3)) == D(1500 - 250) / COIN

    addr1 = to_cash_address(addr1)
    addr2 = to_cash_address(addr2)
    addr3 = to_cash_address(addr3)

    assert (await bitcoin_cash.get_balance(addr1)) == D(10000 - 2000) / COIN
    assert (await bitcoin_cash.get_balance(addr2)) == D(500 - 250) / COIN
    assert (await bitcoin_cash.get_balance(addr3)) == D(1500 - 250) / COIN


async def test_basic_bitcoin_cash_zero_wallet(fee_mocker):
    bitcoin_cash = BitcoinCash()
    addr1, priv1 = await bitcoin_cash.create_wallet()
    addr2, priv2 = await bitcoin_cash.create_wallet()

    assert bitcoin_cash.validate_addr(addr1)
    assert bitcoin_cash.validate_addr(addr2)

    await bitcoin_cash.post('sendtoaddress', addr1, 10000 / COIN)
    await bitcoin_cash.post('generate', 1)
    assert (await bitcoin_cash.get_balance(addr1)) == D(10000) / COIN

    tx_id = await bitcoin_cash.send_money(priv1, [(addr2, D(10000) / COIN)])
    assert tx_id

    await bitcoin_cash.post('generate', 1)
    # 500 fee splited equally onto 2 recievers:
    assert (await bitcoin_cash.get_balance(addr2)) == D(10000 - 500) / COIN


async def test_new_wallet_empty():
    bitcoin_cash = BitcoinCash()
    addr1, priv1 = await bitcoin_cash.create_wallet()
    assert bitcoin_cash.validate_addr(addr1)
    assert (await bitcoin_cash.get_balance(addr1)) == D(0)


async def test_insufficient_amount():
    bitcoin_cash = BitcoinCash()
    addr1, priv1 = await bitcoin_cash.create_wallet()
    addr2, priv2 = await bitcoin_cash.create_wallet()
    assert bitcoin_cash.validate_addr(addr1)
    await bitcoin_cash.post('sendtoaddress', addr1, 10000 / COIN)
    with pytest.raises(NotEnoughAmountError):
        await bitcoin_cash.send_money(priv1, [(addr2, D(15000) / COIN)])


async def test_insufficient_amount_to_cover_fee():
    bitcoin_cash = BitcoinCash()
    addr1, priv1 = await bitcoin_cash.create_wallet()
    addr2, priv2 = await bitcoin_cash.create_wallet()
    assert bitcoin_cash.validate_addr(addr1)
    await bitcoin_cash.post('sendtoaddress', addr1, 10000 / COIN)
    with pytest.raises(NotEnoughAmountError):
        await bitcoin_cash.send_money(priv1, [(addr2, D(10001) / COIN)])
