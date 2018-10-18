import asyncio

import dotenv

dotenv.load_dotenv('.test.env')  # noqa

import pytest

from moonwalking import main
from moonwalking import settings

from eth_keys.datatypes import PublicKey, PrivateKey
from eth_utils.currency import to_wei
from eth_utils.address import to_checksum_address


def private_key_to_checksum_address(key):
    if key.startswith('0x'):
        key = key[2:]
    return PublicKey.from_private(
        PrivateKey(bytes.fromhex(key))
    ).to_checksum_address()


class EthHelperMixin:
    MAIN_ADDR = private_key_to_checksum_address(settings.BUFFER_ETH_PRIV)

    @classmethod
    def register(cls):
        pass


class EthHelper(EthHelperMixin, main.Ethereum):
    async def send_money(self, addr, amount):
        nonce = await self.post(
            'eth_getTransactionCount',
            self.MAIN_ADDR,
        )
        tx = {
            'from': self.MAIN_ADDR,
            'to': addr,
            'value': to_wei(amount, 'ether'),
            'gas': 22000,
            'gasPrice': to_wei(8, 'gwei'),
            'chainId': 1,
            'nonce': nonce,
        }
        return await self.post('eth_sendTransaction', tx)


class LndHelper(EthHelperMixin, main.Lendingblock):
    async def create_contract(self):
        tx_hash = await self.post('eth_sendTransaction', {
            'from': self.MAIN_ADDR,
            'gas': 4000000,
            'gasPrice': 100,
            'data': settings.LND_CONTRACT['bytecode'],
        })
        receipt = await self.post(
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
