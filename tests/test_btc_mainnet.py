import pycoin

from moonwalking.main import Bitcoin


async def test_bitcoin_create_wallet():
    bitcoin = Bitcoin()
    bitcoin.NET_WALLET = 'btc'
    addr1, priv1 = await bitcoin.create_wallet()

    assert pycoin.encoding.is_hashed_base58_valid(addr1) is True
    assert pycoin.encoding.is_hashed_base58_valid(priv1) is True
    assert pycoin.encoding.is_valid_bitcoin_address(addr1) is True
    assert pycoin.encoding.is_valid_wif(priv1) is True
    assert pycoin.key.validate.is_wif_valid(priv1) == 'BTC'
    assert pycoin.key.validate.is_private_bip32_valid(priv1) is None
    assert pycoin.key.validate.is_address_valid(addr1) == 'BTC'
    assert pycoin.key.Key.from_text(priv1).address() == addr1
    assert addr1[0] == '1'
    assert priv1[0] in ['L', 'K']

    priv2 = 'L3XJp5UxLouN3Mw6ycJ4fJT678gjhERx9yfTfzYpVNqom1g7i5Nu'
    addr2 = '1BTm2i94LVDs6vMkf4qDs1Ato1NszQiE4z'
    assert pycoin.key.Key.from_text(priv2).address() == addr2


async def test_bitcoin_validate_addr(mocker):
    bitcoin = Bitcoin()
    mocker.patch('moonwalking.settings.USE_TESTNET', None)

    # testnet address
    assert bitcoin.validate_addr('mn8eCaT46d8mEn62ussMtE467J4mSgu5zA') is None
    # P2PKH address starting with 1
    assert bitcoin.validate_addr('1BTm2i94LVDs6vMkf4qDs1Ato1NszQiE4z') == \
        '1BTm2i94LVDs6vMkf4qDs1Ato1NszQiE4z'
    # all lowercase
    assert bitcoin.validate_addr('1btm2i94lvds6vmkf4qds1ato1nszqie4z') is None
    # all uppercase
    assert bitcoin.validate_addr('1BTM2I94LVDS6VMKF4QDS1ATO1NSZQIE4Z') is None
    # wrong checksum
    assert bitcoin.validate_addr('1BTm2i94LVDs6vMkf4qDs1Ato1NszQiE4a') is None
    # P2SH address
    assert bitcoin.validate_addr('3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy') == \
        '3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy'
    # wrong checksum
    assert bitcoin.validate_addr('3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLa') is None
    # Bech32 address
    assert bitcoin.validate_addr(
        'bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq'
        ) is None
    # litecoin address
    assert bitcoin.validate_addr('LcNs562P7ZEtAhRcQTabwNEa9QETvEiLzz') is None
    # litecoin P2SH address
    assert bitcoin.validate_addr('MV5rN5EcX1imDS2gEh5jPJXeiW5QN8YrK3') is None
