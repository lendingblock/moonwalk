from pycoin.tx.Tx import Tx
from pycoin.key.validate import is_address_valid

from moonwalk import settings
from .fee import FeeStation
from .bitcoin_generic import BitcoinGenericProxy


class BitcoinProxy(BitcoinGenericProxy):

    MAX_FEE = 100
    URL = settings.BITCOIN_URL
    NET_WALLET = 'btctest' if settings.USE_TESTNET else 'btc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    NETCODE = 'XTN' if settings.USE_TESTNET else 'BTC'

    async def calc_fee(self, tx: Tx) -> int:
        if not settings.BITCOIN_FEE:
            fee_station = FeeStation('btc')
            transaction_fee = await fee_station.get_fee()
            transaction_fee = min(self.MAX_FEE, transaction_fee)
        else:
            transaction_fee = int(settings.BITCOIN_FEE)
        tx_size = self.calculate_tx_size(tx)
        return transaction_fee * tx_size

    @staticmethod
    def validate_addr(addr):
        if settings.USE_TESTNET:
            if is_address_valid(addr) == 'XTN':
                return addr
        if is_address_valid(addr) == 'BTC':
            return addr
