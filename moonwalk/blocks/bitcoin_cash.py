from decimal import Decimal as D

from aiohttp.client import ClientSession
from bitcoin.core import COIN
from cashaddress.convert import to_legacy_address, is_valid
from bitcash.network.meta import Unspent
from bitcash.wallet import PrivateKey, PrivateKeyTestnet
from bitcash.transaction import create_p2pkh_transaction, estimate_tx_fee

from moonwalk import settings
from .base import NotEnoughAmountError


class BitcoinCashProxy:

    URL = settings.BITCOIN_CASH_URL
    NET_WALLET = 'btctest' if settings.USE_TESTNET else 'btc'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    KEY_CLASS = PrivateKeyTestnet if settings.USE_TESTNET else PrivateKey

    def get_data(self, method, *params):
        return {
            'version': '1.1',
            'method': method,
            'params': list(params),
            'id': self.NETWORK
        }

    @staticmethod
    def calc_fee(n_in, n_out):
        return estimate_tx_fee(
            n_in,
            n_out,
            int(settings.BITCOIN_CASH_FEE),
            False,
        )

    async def post(self, *args):
        async with ClientSession() as session:
            async with session.post(self.URL, json=self.get_data(*args)) as res:
                resp_dict = await res.json()
                return resp_dict['result']

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

    async def create_wallet(self):
        key = self.KEY_CLASS()
        addr = to_legacy_address(key.address)
        await self.post('importaddress', addr, '', False)
        return addr, key.to_wif()

    @staticmethod
    def normalize_decimal(d):
        return d.to_integral() if d == d.to_integral() else d.normalize()

    async def get_balance(self, addr):
        unspent_list = await self._get_raw_unspent_list(addr)
        d = D(str(sum(
            D(str(unspent['amount'])) for unspent in unspent_list
        )))
        return self.normalize_decimal(d)

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

    @staticmethod
    def validate_addr(addr):
        if is_valid(addr):
            return to_legacy_address(addr)
