import logging
from decimal import Decimal as D

from aiohttp.client import ClientSession

from eth_abi.abi import decode_abi
from eth_account import Account
from eth_hash.auto import keccak
from eth_utils import from_wei, to_checksum_address, is_address
from eth_utils.currency import to_wei

from hexbytes.main import HexBytes

from .. import settings
from .exc import (
    EthereumError, ReplacementTransactionError, NotEnoughAmountError
)
from .fee import FeeStation
from .base import BaseBlock

logger = logging.getLogger(__name__)
DECIMALS = pow(10, 18)


class EthereumGeneric(BaseBlock):
    MAX_FEE = 100
    URL = settings.ETH_URL
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'
    MIN_GAS = 21000
    MAX_GAS = 100000

    def get_data(self, method, *params):
        return {
            'jsonrpc': '2.0',
            'method': method,
            'params': list(params),
            'id': self.NETWORK
        }

    async def post(self, *args):
        async with ClientSession() as sess:
            async with sess.post(self.URL, json=self.get_data(*args)) as res:
                resp_dict = await res.json()
                result = resp_dict.get('result')
                error = resp_dict.get('error')
                if error:
                    message = error.get('message')
                    if message == 'replacement transaction underpriced':
                        raise ReplacementTransactionError
                    raise EthereumError(data=resp_dict)
                return result

    async def get_gas_price(self) -> int:
        if not settings.ETH_FEE:
            fee_station = FeeStation('eth')
            transaction_fee = await fee_station.get_fee()
            return min(self.MAX_FEE, transaction_fee)
        return to_wei(int(settings.ETH_FEE), 'gwei')

    async def get_eth_balance(self, addr):
        balance = await self.post('eth_getBalance', addr, 'latest')
        return D(from_wei(int(balance, 16), 'ether'))

    async def send_single_transaction(
        self,
        priv,
        addr_to,
        amount,
        nonce,
        data='',
        subtract_fee=False,
        max_attempts=10,
    ):
        if max_attempts < 1:
            return
        tx_dict = await self.get_transaction_dict(
            priv,
            addr_to,
            amount,
            nonce,
            data,
            subtract_fee,
        )
        tx_hex = Account.signTransaction(tx_dict, priv).rawTransaction.hex()
        try:
            return await self.post('eth_sendRawTransaction', tx_hex)
        except ReplacementTransactionError:
            max_attempts -= 1
            nonce += 1
            return await self.send_single_transaction(
                priv,
                addr_to,
                amount,
                nonce,
                data,
                subtract_fee,
                max_attempts=max_attempts
            )

    async def get_transaction_dict(self, priv, addr_to, amount, nonce, data,
                                   subtract_fee):
        if data:  # Pull this out.
            gas = self.MAX_GAS
        else:
            get_code = await self.post('eth_getCode', addr_to, 'latest')
            gas = 50000 if len(get_code) > 3 else self.MIN_GAS

        gas_price = await self.get_gas_price()
        amount = to_wei(amount, 'ether')
        if subtract_fee:
            fee = gas * gas_price
            amount -= fee
        return {
            'from': Account.privateKeyToAccount(priv).address,
            'to': addr_to,
            'value': amount,
            'gas': gas,
            'gasPrice': gas_price,
            'data': data,
            'chainId': int(settings.ETH_CHAIN_ID),
            'nonce': nonce
        }

    def make_lnd_transfer_data(self, addr_to, amount):
        # Todo: Generalise to any contract.
        method_hash = self.get_method_hash('transfer')
        addr_hash = self.get_addr_hash(addr_to)
        amount_hash = self.get_amount_hash(amount)
        return method_hash + addr_hash + amount_hash

    async def validate_balance(self, priv, addrs):
        addr_from = Account.privateKeyToAccount(priv).address
        balance = await self.get_eth_balance(addr_from)
        addr, amount = addrs[0]
        if amount > balance:
            raise NotEnoughAmountError()

    async def get_transaction_count(self, addr_from):
        nonce = await self.post('eth_getTransactionCount', addr_from,
                                'pending')
        return int(nonce, 16)

    async def send_eth(self, priv, addrs):
        # Todo: Move to eth currency class.
        await self.validate_balance(priv, addrs)
        addr_from = Account.privateKeyToAccount(priv).address
        nonce = await self.get_transaction_count(addr_from)
        tx_ids = [
            await self.send_single_transaction(priv, addr, amount, nonce + i,
                                               subtract_fee=True)
            for i, (addr, amount) in enumerate(addrs)
        ]
        return tx_ids

    async def send_all_eth_to_buffer_wallet(self, priv):
        addr = Account.privateKeyToAccount(priv).address
        buffer_addr = Account.privateKeyToAccount(
            settings.BUFFER_ETH_PRIV
        ).address
        balance = await self.get_eth_balance(addr)
        return await self.send_eth(priv, [(buffer_addr, balance)])

    def validate_addr(self, addr):
        if is_address(addr):
            return addr

    def create_addr(self):
        account = Account().create()
        return account.address, account.privateKey.hex()

    @staticmethod
    def get_contract_addr():
        """
        to make tests mocking easier
        """
        return to_checksum_address(settings.LND_CONTRACT_ADDR)

    def get_method_hash(self, method):
        method_sig = self.get_method_signature(method)
        if method_sig:
            return '0x' + keccak(method_sig.encode()).hex()[:8]

    @staticmethod
    def get_addr_hash(addr):
        if addr.startswith('0x'):
            return addr.lower()[2:].zfill(64)
        return ''

    @staticmethod
    def get_amount_hash(num):
        return hex(int(num * DECIMALS))[2:].zfill(64)

    @staticmethod
    def get_method_signature(method_name):
        method_abi = next(x for x in settings.LND_CONTRACT['abi']
                          if x.get('name') == method_name)
        args = ','.join(i['type'] for i in method_abi.get('inputs', ()))
        return f'{method_name}({args})'

    async def call_contract_method(self, method, to_int=False,
                                   to_string=False):
        contract_address = self.get_contract_addr()
        result = await self.post('eth_call', {
            'to': contract_address,
            'data': self.get_method_hash(method)
        }, 'latest')
        if to_int:
            return int(result, 16)
        elif to_string:
            return decode_abi(['string'], HexBytes(result))[0].decode()
        return result
