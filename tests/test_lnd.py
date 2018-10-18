from decimal import Decimal as D

from eth_account import Account

from moonwalking.main import Lendingblock


PRIV_KEY = '0x869844d42d74171d1c5e71ecd8964118e68f610af94047fd1e98afb4df1c5e1b'


async def test_lnd(eth_helper, lnd_helper, fee_mocker):
    lnd = Lendingblock()
    account = Account.privateKeyToAccount(PRIV_KEY).address

    # initial balance is 1 billion which is pow(10, 9)
    decimals = await lnd.call_contract_method('decimals', to_int=True)
    assert decimals == 18
    initial_balance = await lnd.get_balance(account)
    total_supply = await lnd.call_contract_method(
        'totalSupply',
        to_int=True,
    )
    assert initial_balance == D(total_supply / pow(10, decimals))
    assert initial_balance == D(pow(10, 9))

    name = await lnd.call_contract_method(
        'name',
        to_string=True,
    )
    assert name == 'Lendingblock'

    symbol = await lnd.call_contract_method(
        'symbol',
        to_string=True,
    )
    assert symbol == 'LND'

    addr1, priv1 = await lnd.create_wallet()
    addr2, priv2 = await lnd.create_wallet()
    addr3, priv3 = await lnd.create_wallet()

    assert lnd.validate_addr(addr1)
    assert lnd.validate_addr(addr2)
    assert lnd.validate_addr(addr3)

    # we need some ETH to pay transaction fees
    assert await eth_helper.send_money(addr1, D(1))

    tx_ids = await lnd.send_money(
        PRIV_KEY,
        [(addr1, D(1000)), (addr2, D(2000))],
    )

    assert len(tx_ids) == 2

    # new_balance is 1 billion - 1000 - 2000
    assert await lnd.get_balance(account) == D(1000000000 - 1000 - 2000)
    assert await lnd.get_balance(addr1) == D(1000)
    assert await lnd.get_balance(addr2) == D(2000)
    assert await lnd.get_balance(addr3) == D(0)

    assert await lnd.send_money(priv1, [(addr3, D(400))])
    assert await lnd.get_balance(addr1) == D(1000 - 400)
    assert await lnd.get_balance(addr3) == D(400)


async def test_get_addr_hash():
    addr = '0x4092678e4E78230F46A1534C0fbc8fA39780892B'
    lnd = Lendingblock()
    assert lnd.get_addr_hash(addr) == \
        '0000000000000000000000004092678e4e78230f46a1534c0fbc8fa39780892b'
    assert lnd.get_addr_hash(addr[2:]) == ''
