from decimal import Decimal as D

from bitcoin.core import COIN

from moonwalking.main import Litecoin


async def test_basic_ltc_ops(fee_mocker):
    ltc = Litecoin()
    addr1, priv1 = await ltc.create_wallet()
    addr2, priv2 = await ltc.create_wallet()
    addr3, priv3 = await ltc.create_wallet()

    assert ltc.validate_addr(addr1)
    assert ltc.validate_addr(addr2)
    assert ltc.validate_addr(addr3)

    await ltc.post('sendtoaddress', addr1, 100000 / COIN)
    await ltc.post('generate', 1)
    assert (await ltc.get_balance(addr1)) == D(100000) / COIN

    tx_id = await ltc.send_money(
        priv1,
        [(addr2, D(5000) / COIN), (addr3, D(15000) / COIN)]
    )
    assert tx_id
    await ltc.post('generate', 1)

    # 500 fee splited equally onto 2 recievers:
    assert (await ltc.get_balance(addr1)) == D(100000 - 20000) / COIN
    assert (await ltc.get_balance(addr2)) == D(5000 - 250) / COIN
    assert (await ltc.get_balance(addr3)) == D(15000 - 250) / COIN
