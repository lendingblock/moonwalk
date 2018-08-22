from eth_utils.address import is_address
from cashaddress.convert import is_valid
from pycoin.key.validate import is_address_valid


class CcyHelper:
    def __init__(self, ccy, use_testnet=False):
        self.ccy = ccy
        self.network = 'testnet' if use_testnet else 'mainnet'

    def validate_addr(self, addr):
        try:
            return getattr(self, f'validate_{self.ccy.lower()}')(addr)
        except AttributeError:
            return False

    def validate_btc(self, addr):
        if self.network == 'testnet':
            return is_address_valid(addr) == 'XTN'
        return is_address_valid(addr) == 'BTC'

    def validate_ltc(self, addr):
        if self.network == 'testnet':
            return is_address_valid(addr) == 'XTN'
        return is_address_valid(addr) == 'LTC'

    @staticmethod
    def validate_eth(addr):
        return is_address(addr)

    @staticmethod
    def validate_bch(addr):
        return is_valid(addr)

    @staticmethod
    def validate_lnd(addr):
        return is_address(addr)
