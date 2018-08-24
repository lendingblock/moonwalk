from pycoin.tx.Tx import Tx
from pycoin.key.validate import is_address_valid
from .. import settings
from .bitcoin_generic import BitcoinGenericProxy


class LitecoinProxy(BitcoinGenericProxy):

    URL = settings.LITECOIN_URL
    NET_WALLET = 'ltctest' if settings.USE_TESTNET else 'ltc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    NETCODE = 'XTN' if settings.USE_TESTNET else 'LTC'

    async def calc_fee(self, tx: Tx) -> int:
        tx_size = self.calculate_tx_size(tx)
        return int(settings.LITECOIN_FEE) * tx_size

    @classmethod
    def validate_addr(cls, addr):
        if settings.USE_TESTNET:
            if is_address_valid(addr) == 'XTN':
                return addr
        if is_address_valid(addr) == 'LTC':
            return addr
