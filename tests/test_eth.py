from decimal import Decimal as D

import pytest
from eth_utils import to_checksum_address, from_wei

from moonwalking import wallets
from moonwalking.main import Ethereum
from moonwalking.blocks.exc import NotEnoughAmountError


def test_create_addr():
    addr, pk = wallets.create_addr('eth')
    assert addr
    assert pk


async def test_not_enough_amount(eth_helper):
    eth = Ethereum()
    addr1, priv1 = await wallets.create_wallet('eth')
    addr2, priv2 = await eth.create_wallet()

    assert await eth.get_balance(addr1) == D(0)
    assert await eth_helper.send_money(addr1, D(1))
    assert await eth.get_balance(addr1) == D(1)

    with pytest.raises(NotEnoughAmountError):
        await eth.send_money(priv1, [(addr2, D(2))])


async def test_send_money(eth_helper, fee_mocker):
    eth = Ethereum()
    addr1, priv1 = await eth.create_wallet()
    addr2, priv2 = await eth.create_wallet()

    assert await eth.get_balance(addr1) == 0
    assert await eth_helper.send_money(addr1, D(1))
    assert await eth.get_balance(addr1) == D(1)
    assert await eth.get_balance(addr2) == 0
    assert await eth.send_money(priv1, [(addr2, D('0.5'))])
    fee = D('0.00021')
    assert await eth.get_balance(addr1) == D('0.5')
    assert await eth.get_balance(addr2) == D('0.5') - fee


async def test_send_money_to_multiple_recipients(eth_helper, fee_mocker):
    eth = Ethereum()
    fee = D('0.00021')
    addr1, priv1 = await eth.create_wallet()
    addr2, priv2 = await eth.create_wallet()
    addr3, priv3 = await eth.create_wallet()
    addr4, priv4 = await eth.create_wallet()

    assert await eth.get_balance(addr1) == 0
    assert await eth_helper.send_money(addr1, D(1))
    assert await eth.get_balance(addr1) == D(1)
    assert await eth.get_balance(addr2) == 0
    assert await eth.get_balance(addr3) == 0
    assert await eth.send_money(priv1, [(addr2, D('0.1')), (addr3, D('0.2'))])
    assert await eth.get_balance(addr1) == D('0.7')
    assert await eth.get_balance(addr2) == D('0.1') - fee
    assert await eth.get_balance(addr3) == D('0.2') - fee
    assert await eth.send_money(priv1, [(addr4, D('0.7'))])
    assert await eth.get_balance(addr1) == 0
    assert await eth.get_balance(addr4) == D('0.7') - fee


async def test_send_money_contract(eth_helper, fee_mocker):
    eth = Ethereum()
    addr1, priv1 = await eth.create_wallet()

    assert await eth_helper.send_money(addr1, D(10))
    assert await eth.get_balance(addr1) == D(10)

    # deploy a simple contract that accepts eth
    tx_hash = await eth_helper.post('eth_sendTransaction', {
        'from': eth_helper.MAIN_ADDR,
        'gas': 4000000,
        'gasPrice': 20,
        'data': (
            '0x608060405234801561001057600080fd5b50336000806101000'
            'a81548173ffffffffffffffffffffffffffffffffffffffff02191'
            '6908373ffffffffffffffffffffffffffffffffffffffff1602179'
            '05550610292806100606000396000f300608060405260043610610'
            '04c576000357c01000000000000000000000000000000000000000'
            '00000000000000000900463ffffffff1680633ccfd60b1461009c5'
            '780638da5cb5b146100b3575b3373fffffffffffffffffffffffff'
            'fffffffffffffff167fd4f43975feb89f48dd30cabbb32011045be'
            '187d1e11c8ea9faa43efc352825193460405180828152602001915'
            '05060405180910390a2005b3480156100a857600080fd5b506100b'
            '161010a565b005b3480156100bf57600080fd5b506100c86102415'
            '65b604051808273fffffffffffffffffffffffffffffffffffffff'
            'f1673ffffffffffffffffffffffffffffffffffffffff168152602'
            '00191505060405180910390f35b6000809054906101000a900473f'
            'fffffffffffffffffffffffffffffffffffffff1673fffffffffff'
            'fffffffffffffffffffffffffffff163373fffffffffffffffffff'
            'fffffffffffffffffffff1614151561016557600080fd5b6000809'
            '054906101000a900473fffffffffffffffffffffffffffffffffff'
            'fffff1673ffffffffffffffffffffffffffffffffffffffff16337'
            '3ffffffffffffffffffffffffffffffffffffffff161415156101c'
            '057600080fd5b6000809054906101000a900473fffffffffffffff'
            'fffffffffffffffffffffffff1673fffffffffffffffffffffffff'
            'fffffffffffffff166108fc3073fffffffffffffffffffffffffff'
            'fffffffffffff16319081150290604051600060405180830381858'
            '888f1935050505015801561023e573d6000803e3d6000fd5b50565'
            'b6000809054906101000a900473fffffffffffffffffffffffffff'
            'fffffffffffff16815600a165627a7a7230582085608321fc053d1'
            '45b06de95c945cafcb58eceb5fbd45a892860ac0c5ceae0c50029'
        )
    })
    receipt = await eth_helper.post(
        'eth_getTransactionReceipt',
        tx_hash
    )
    addr2 = to_checksum_address(receipt['contractAddress'])
    assert await eth.send_money(priv1, [(addr2, D('0.5'))])
    fee = D(50000) * D(from_wei(10, 'gwei'))
    assert await eth.get_balance(addr2) == D('0.5') - fee
