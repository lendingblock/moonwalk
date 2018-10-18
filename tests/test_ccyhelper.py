from moonwalking.blocks.ccyhelper import CcyHelper


def test_ccyhelper():
    ccyhelper = CcyHelper('btc', use_testnet=True)
    assert ccyhelper.validate_addr('mtXWDB6k5yC5v7TcwKZHB89SUp85yCKshy')

    ccyhelper = CcyHelper('btc')
    assert not ccyhelper.validate_addr('mtXWDB6k5yC5v7TcwKZHB89SUp85yCKshy')

    ccyhelper = CcyHelper('btc')
    assert ccyhelper.validate_addr('1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX')

    ccyhelper = CcyHelper('ltc')
    assert ccyhelper.validate_addr('LWSygPfS6FEiDqdj2xmVF8CSZJREo4LbKd')

    ccyhelper = CcyHelper('ltc', use_testnet=True)
    assert ccyhelper.validate_addr('mgTbDyNGwJeewjdXmU9cRQe8WDauVqn4WK')

    ccyhelper = CcyHelper('bch')
    assert ccyhelper.validate_addr('mhstAGNEZYNxwpwgAqwX31sK2TK7SntHCK')

    ccyhelper = CcyHelper('eth')
    assert ccyhelper.validate_addr(
        '0x0dE0BCb0703ff8F1aEb8C892eDbE692683bD8030'
    )

    ccyhelper = CcyHelper('lnd')
    assert ccyhelper.validate_addr(
        '0x0dE0BCb0703ff8F1aEb8C892eDbE692683bD8030'
    )

    ccyhelper = CcyHelper('fake_currency')
    assert not ccyhelper.validate_addr('1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX')
