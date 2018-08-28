import asyncio
import os

import pytest
from eth_utils.currency import to_wei
from eth_utils.address import to_checksum_address

from moonwalk.blocks.eth import EthereumProxy
from moonwalk import settings


class EthHelper:

    def __init__(self):
        self.proxy = EthereumProxy()

    async def send_money(self, addr, amount):
        nonce = await self.proxy.post(
            'eth_getTransactionCount',
            to_checksum_address(settings.MAIN_ETH_ADDR),
        )
        tx = {
            'from': settings.MAIN_ETH_ADDR,
            'to': addr,
            'value': to_wei(amount, 'ether'),
            'gas': 22000,
            'gasPrice': to_wei(8, 'gwei'),
            'chainId': 1,
            'nonce': nonce,
        }
        return await self.proxy.post('eth_sendTransaction', tx)


class LndHelper:

    cd = os.path.dirname
    FIXTURE_DIR = os.path.join(cd(cd(__file__)), 'fixtures')
    COMPILED_CONTRACT_JSON = os.path.join(
        FIXTURE_DIR,
        'LendingBlockToken.json',
    )

    def __init__(self):
        self.proxy = EthereumProxy()

    async def create_contract(self):
        tx_hash = await self.proxy.post('eth_sendTransaction', {
            'from': to_checksum_address(settings.MAIN_LND_ADDR),
            'gas': 4000000,
            'gasPrice': 100,
            'data': settings.LND_CONTRACT['bytecode'],
        })
        receipt = await self.proxy.post(
            'eth_getTransactionReceipt',
            tx_hash
        )
        return receipt['contractAddress']


@pytest.fixture(autouse=True)
def loop():
    """Return an instance of the event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def eth_helper():
    yield EthHelper()


@pytest.fixture()
async def lnd_helper(mocker):
    lnd_helper = LndHelper()
    contract_addr = await lnd_helper.create_contract()
    mocker.patch('moonwalk.settings.LND_CONTRACT_ADDR', contract_addr)
    yield lnd_helper


async def calc_fee_mock(self, tx):
    return 500


async def get_gas_price_mock(self):
    return to_wei(10, 'gwei')


@pytest.fixture()
async def fee_mocker(mocker):
    mocker.patch(
        'moonwalk.blocks.bitcoin.BitcoinProxy.calc_fee',
        calc_fee_mock
    )
    mocker.patch(
        'moonwalk.blocks.ltc.LitecoinProxy.calc_fee',
        calc_fee_mock
    )
    mocker.patch(
        'moonwalk.blocks.bitcoin_cash.BitcoinCashProxy.calc_fee',
        lambda x, y, z: 500
    )
    mocker.patch(
        'moonwalk.blocks.eth.EthereumProxy.get_gas_price',
        get_gas_price_mock
    )
