import re

import eth_utils
from eth_account import Account

from moonwalking.main import Lendingblock
from moonwalking import wallets


async def test_lnd_create_wallet(fee_mocker, lnd_helper):
    lnd = Lendingblock()
    addr1, priv1 = await lnd.create_wallet()

    pattern_address = re.compile('^(0x)[0-9a-fA-F]{40}$')
    pattern_private = re.compile('^(0x)[0-9a-fA-F]{64}$')
    assert pattern_address.match(addr1)
    assert pattern_private.match(priv1)
    assert eth_utils.is_checksum_address(addr1) is True
    assert Account.privateKeyToAccount(priv1).address == addr1

    priv2 = (
        '0xb25c7db31feed9122727bf0939dc769a96564b2de4c4726d035b36ecf1e5b364')
    addr2 = '0x5ce9454909639D2D17A3F753ce7d93fa0b9aB12E'
    assert Account.privateKeyToAccount(priv2).address == addr2


async def test_lnd_validate_addr():
    lnd = Lendingblock()

    # do not pad missing length
    assert lnd.validate_addr('0x0') is None
    # all uppercase valid checksummed
    assert wallets.validate_addr(
        'lnd',
        '0x52908400098527886E0F7030069857D2E4169EE7'
        ) == '0x52908400098527886E0F7030069857D2E4169EE7'
    # all lowercase valid checksummed
    assert lnd.validate_addr(
        '0xde709f2102306220921060314715629080e2fb77'
        ) == '0xde709f2102306220921060314715629080e2fb77'
    # normal checksummed address
    assert lnd.validate_addr(
        '0xd3CdA913deB6f67967B99D67aCDFa1712C293601'
        ) == '0xd3CdA913deB6f67967B99D67aCDFa1712C293601'
    # wrong checksummed address
    assert lnd.validate_addr(
        '0xd3cdA913deB6f67967B99D67aCDFa1712C293601'
        ) is None
    # all lowercase
    assert lnd.validate_addr(
        '0xd3cda913deb6f67967b99d67acdfa1712c293601'
        ) == '0xd3cda913deb6f67967b99d67acdfa1712c293601'
    # all uppercase
    assert lnd.validate_addr(
        '0xD3CDA913DEB6F67967B99D67ACDFA1712C293601'
        ) == '0xD3CDA913DEB6F67967B99D67ACDFA1712C293601'
    # starts with 00
    assert lnd.validate_addr(
        '0x00908400098527886E0F7030069857d2e4169eE7'
        ) == '0x00908400098527886E0F7030069857d2e4169eE7'
    # do not pad missing length
    assert lnd.validate_addr(
        '0x908400098527886E0F7030069857d2e4169eE7'
        ) is None
    # ends with 00
    assert lnd.validate_addr(
        '0x52908400098527886e0F7030069857d2E4169e00'
        ) == '0x52908400098527886e0F7030069857d2E4169e00'
    # do not pad missing length
    assert lnd.validate_addr(
        '0x52908400098527886e0F7030069857d2E4169e'
        ) is None
