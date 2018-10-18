import logging
from decimal import Decimal as D

from bitcash import PrivateKeyTestnet, PrivateKey
from bitcash.network.meta import Unspent
from bitcash.transaction import estimate_tx_fee, create_p2pkh_transaction
from bitcoin.core import COIN

from cashaddress.convert import is_valid, to_legacy_address

from eth_account import Account
from eth_utils import from_wei

from pycoin.key.validate import is_address_valid
from pycoin.tx import Tx

from . import settings
from .blocks.base import BaseBlock
from .blocks.bitcoin_generic import BitcoinGeneric
from .blocks.eth_generic import EthereumGeneric
from .blocks.exc import NotEnoughAmountError
from .blocks.fee import FeeStation
from .utils import GeneralError, rand_str

logger = logging.getLogger(__name__)

DECIMALS = pow(10, 18)  # Todo: Rename me pls.
BLOCKS = BaseBlock.BLOCKS


class BlockError(Exception):
    pass


class WrongKeyError(BlockError):
    pass


class WrongAddressError(BlockError):
    pass


class InsufficientFoundsError(BlockError):
    pass


class Dummycoin(BaseBlock):
    """used in tests"""
    ADDRESSES = {}
    PRIV_KEYS = {}

    def validate_addr(self, addr):
        if addr in self.ADDRESSES:
            return addr

    def create_addr(self):
        addr = rand_str()
        priv_key = f'1_{addr}'
        self.ADDRESSES[addr] = D(0)
        self.PRIV_KEYS[priv_key] = addr
        return addr, priv_key

    async def create_wallet(self):
        return self.create_addr()

    async def send_money(self, priv, addrs):
        for addr, amount in addrs:
            if not self.validate_addr(addr):
                raise WrongAddressError(addr)

        wallet_addr = priv[2:]
        balance = self.ADDRESSES[wallet_addr]

        sum_amounts = sum(addr[1] for addr in addrs)

        if balance < sum_amounts:
            raise InsufficientFoundsError(str(balance))

        self.ADDRESSES[wallet_addr] -= sum_amounts
        for addr, amount in addrs:
            self.ADDRESSES[addr] += amount

        return rand_str()

    async def get_balance(self, addr):
        if addr not in self.ADDRESSES:
            raise WrongAddressError(addr)
        return self.ADDRESSES[addr]


class Bitcoin(BitcoinGeneric):
    CCY = 'btc'
    MAX_FEE = 100
    URL = settings.BITCOIN_URL
    NET_WALLET = 'btctest' if settings.USE_TESTNET else 'btc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    NETCODE = 'XTN' if settings.USE_TESTNET else 'BTC'

    def validate_addr(self, addr):
        if settings.USE_TESTNET:
            if is_address_valid(addr) == 'XTN':
                return addr
        if is_address_valid(addr) == 'BTC':
            return addr

    async def calc_fee(self, tx: Tx) -> int:
        if not settings.BITCOIN_FEE:
            fee_station = FeeStation('btc')
            transaction_fee = await fee_station.get_fee()
            transaction_fee = min(self.MAX_FEE, transaction_fee)
        else:
            transaction_fee = int(settings.BITCOIN_FEE)
        tx_size = self.calculate_tx_size(tx)
        return transaction_fee * tx_size


class Litecoin(BitcoinGeneric):
    CCY = 'ltc'
    URL = settings.LITECOIN_URL
    NET_WALLET = 'ltctest' if settings.USE_TESTNET else 'ltc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    NETCODE = 'XTN' if settings.USE_TESTNET else 'LTC'

    def validate_addr(self, addr):
        if settings.USE_TESTNET:
            if is_address_valid(addr) == 'XTN':
                return addr
        if is_address_valid(addr) == 'LTC':
            return addr

    async def calc_fee(self, tx: Tx) -> int:
        tx_size = self.calculate_tx_size(tx)
        return int(settings.LITECOIN_FEE) * tx_size


class BitcoinCash(BitcoinGeneric):
    CCY = 'bch'
    URL = settings.BITCOIN_CASH_URL
    NET_WALLET = 'btctest' if settings.USE_TESTNET else 'btc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    KEY_CLASS = PrivateKeyTestnet if settings.USE_TESTNET else PrivateKey

    def validate_addr(self, addr):
        if is_valid(addr):
            return to_legacy_address(addr)

    async def send_money(self, priv, addrs):
        key = self.KEY_CLASS(priv)
        addr_from = to_legacy_address(key.address)
        unspent_obj_list = await self._get_obj_unspent_list(addr_from)

        payables = [
            (to_legacy_address(addr), amount * COIN)
            for addr, amount in addrs
        ]
        total_out = sum(amount for addr, amount in payables)
        total_unspent = sum(D(unspent.amount) for unspent in unspent_obj_list)
        remaining = total_unspent - total_out

        if total_out > total_unspent:
            raise NotEnoughAmountError()

        fee = self.calc_fee(len(unspent_obj_list), len(addrs))
        fee_per_tx_out, extra_count = divmod(fee, len(addrs))

        calc_addrs = []
        for addr, amount in payables:
            amount -= fee_per_tx_out
            if extra_count > 0:
                amount -= 1
            if amount < 1:
                raise NotEnoughAmountError()
            calc_addrs.append((addr, int(amount)))
        remaining = int(remaining)
        if remaining > 0:
            calc_addrs.append((addr_from, remaining))

        tx_hex = create_p2pkh_transaction(key, unspent_obj_list, calc_addrs)
        return await self.post('sendrawtransaction', tx_hex)

    async def get_balance(self, addr):
        unspent_list = await self._get_raw_unspent_list(addr)
        d = D(str(sum(
            D(str(unspent['amount'])) for unspent in unspent_list
        )))
        return self.normalize_decimal(d)

    def create_addr(self):
        key = self.KEY_CLASS()
        addr = to_legacy_address(key.address)
        return addr, key.to_wif()

    @staticmethod
    def calc_fee(n_in, n_out):
        return estimate_tx_fee(
            n_in,
            n_out,
            int(settings.BITCOIN_CASH_FEE),
            False,
        )

    async def _get_raw_unspent_list(self, addr, confirmations=1):
        addr = to_legacy_address(addr)
        list_unspent = await self.post(
            'listunspent',
            confirmations,
            9999999,
            [addr],
        )
        return list_unspent

    async def _get_obj_unspent_list(self, addr):
        unspent_list = await self._get_raw_unspent_list(addr)
        return [
            Unspent(
                int(D(str(unspent['amount'])) * COIN),
                unspent['confirmations'],
                unspent['scriptPubKey'],
                unspent['txid'],
                unspent['vout']
            )
            for unspent in unspent_list
        ]

    @staticmethod
    def normalize_decimal(d):
        return d.to_integral() if d == d.to_integral() else d.normalize()


class Ethereum(EthereumGeneric):
    CCY = 'eth'

    async def get_balance(self, addr):
        return await self.get_eth_balance(addr)

    async def create_wallet(self):
        return self.create_addr()

    async def send_money(self, priv, addrs):
        return await self.send_eth(priv, addrs)


class Lendingblock(EthereumGeneric):
    CCY = 'lnd'
    LND_WALLETS_TOPUP_TRANS_NO = int(settings.LND_WALLETS_TOPUP_TRANS_NO)

    async def send_money(self, priv, addrs):
        addr_from = Account.privateKeyToAccount(priv).address
        nonce = await self.get_transaction_count(addr_from)
        contract_addr = self.get_contract_addr()
        tx_ids = []
        for i, (addr, amount) in enumerate(addrs):
            data = self.make_lnd_transfer_data(addr, amount)
            tx_id = await self.send_single_transaction(priv, contract_addr, 0,
                                                       nonce + i, data)
            tx_ids.append(tx_id)
        return tx_ids

    async def get_balance(self, addr):
        method_hash = self.get_method_hash('balanceOf')
        addr_hash = self.get_addr_hash(addr)
        result = await self.post('eth_call', {
            'data': method_hash + addr_hash,
            'to': self.get_contract_addr(),
        }, 'latest')
        return D(int(result, 16) / DECIMALS)

    async def create_wallet(self):
        addr, priv = self.create_addr()
        price = await self.get_gas_price()
        single_tx_price = price * self.MAX_GAS
        single_tx_price = from_wei(single_tx_price, 'ether')
        try:
            await self.send_eth(
                settings.BUFFER_ETH_PRIV,
                [(addr, single_tx_price * self.LND_WALLETS_TOPUP_TRANS_NO)],
            )
        except NotEnoughAmountError:
            raise GeneralError("not enough eth in buffer wallet")

        return addr, priv
