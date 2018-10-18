import pycoin

from moonwalking.main import Litecoin


async def test_litecoincreate_wallet():
    ltc = Litecoin()
    ltc.NET_WALLET = 'ltc'
    addr1, priv1 = await ltc.create_wallet()

    assert pycoin.encoding.is_hashed_base58_valid(addr1) is True
    assert pycoin.encoding.is_hashed_base58_valid(priv1) is True
    assert pycoin.key.validate.is_wif_valid(priv1) == 'LTC'
    assert pycoin.key.validate.is_private_bip32_valid(priv1) is None
    assert pycoin.key.validate.is_address_valid(addr1) == 'LTC'
    assert pycoin.key.Key.from_text(priv1).address() == addr1
    assert addr1[0] == 'L'
    assert priv1[0] == 'T'

    priv2 = 'TB648cs5JzYD2QjCbGdTJ4X3BM1uBPrXFjnJq1UNwZ9VTwWvKanv'
    addr2 = 'LcNs562P7ZEtAhRcQTabwNEa9QETvEiLzz'
    assert pycoin.key.Key.from_text(priv2).address() == addr2


async def test_litecoin_validate_addr(mocker):
    ltc = Litecoin()
    mocker.patch('moonwalking.settings.USE_TESTNET', None)

    # testnet address
    assert ltc.validate_addr('mn8eCaT46d8mEn62ussMtE467J4mSgu5zA') is None
    # P2PKH bitcoin address starting with 1
    assert ltc.validate_addr('1BTm2i94LVDs6vMkf4qDs1Ato1NszQiE4z') is None
    # P2SH address
    assert ltc.validate_addr('3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy') is None
    # Bech32 address
    assert ltc.validate_addr(
        'bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq'
        ) is None
    # litecoin address
    assert ltc.validate_addr('LcNs562P7ZEtAhRcQTabwNEa9QETvEiLzz') == \
        'LcNs562P7ZEtAhRcQTabwNEa9QETvEiLzz'
    # all lowercase
    assert ltc.validate_addr('lcns562p7zetahrcqtabwnea9qetveilzz') is None
    # all uppercase
    assert ltc.validate_addr('LCNS562P7ZETAHRCQTABWNEA9QETVEILZZ') is None
    # wrong checksum
    assert ltc.validate_addr('LcNs562P7ZEtAhRcQTabwNEa9QETvEiLza') is None
    # litecoin P2SH address
    assert ltc.validate_addr('MV5rN5EcX1imDS2gEh5jPJXeiW5QN8YrK3') is None
