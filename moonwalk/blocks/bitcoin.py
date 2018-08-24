from aiohttp import ClientSession
from pycoin.tx.Tx import Tx
from pycoin.key.validate import is_address_valid

from .. import settings
from .bitcoin_generic import BitcoinGenericProxy


class BitcoinProxy(BitcoinGenericProxy):

    MAX_FEE = 100
    URL = settings.BITCOIN_URL
    FEE_URL = 'https://bitcoinfees.earn.com/api/v1/fees/recommended'
    NET_WALLET = 'btctest' if settings.USE_TESTNET else 'btc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    NETCODE = 'XTN' if settings.USE_TESTNET else 'BTC'

    async def calc_fee(self, tx: Tx) -> int:
        if not settings.BITCOIN_FEE:
            transaction_fee = await self.get_recommended_transaction_fees()
        else:
            transaction_fee = int(settings.BITCOIN_FEE)
        tx_size = self.calculate_tx_size(tx)
        return transaction_fee * tx_size

    async def get_recommended_transaction_fees(self) -> int:
        async with ClientSession() as session:
            async with session.get(self.FEE_URL) as resp:
                resp_dict = await resp.json()
                fatest_fee = resp_dict['fastestFee']
                return min(self.MAX_FEE, fatest_fee)

    @classmethod
    def validate_addr(cls, addr):
        if settings.USE_TESTNET:
            if is_address_valid(addr) == 'XTN':
                return addr
        if is_address_valid(addr) == 'BTC':
            return addr
