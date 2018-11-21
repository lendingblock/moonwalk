import asyncio

import pytest
from eth_utils.address import to_checksum_address
from eth_utils.currency import to_wei

from moonwalking.testing import create_lnd_contract


@pytest.fixture(autouse=True)
def loop():
    """Return an instance of the event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def lnd_helper(mocker):
    contract_addr = await create_lnd_contract()
    mocker.patch(
        'moonwalking.blocks.eth_generic.EthereumGeneric.get_contract_addr',
        lambda self: to_checksum_address(contract_addr),
    )
    yield lnd_helper


async def calc_fee_mock(self, tx):
    return 500


async def get_gas_price_mock(self):
    return to_wei(10, 'gwei')


@pytest.fixture()
async def fee_mocker(mocker):
    mocker.patch(
        'moonwalking.main.Bitcoin.calc_fee',
        calc_fee_mock
    )
    mocker.patch(
        'moonwalking.main.Litecoin.calc_fee',
        calc_fee_mock
    )
    mocker.patch(
        'moonwalking.main.BitcoinCash.calc_fee',
        lambda x, y, z: 500
    )
    mocker.patch(
        'moonwalking.blocks.eth_generic.EthereumGeneric.get_gas_price',
        get_gas_price_mock
    )
