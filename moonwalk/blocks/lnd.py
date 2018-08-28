from decimal import Decimal as D

from hexbytes.main import HexBytes
from .eth import EthereumProxy
from eth_abi.abi import decode_abi
from eth_account.account import Account
from eth_utils.address import to_checksum_address, is_address
from eth_hash.auto import keccak

from .. import settings


DECIMALS = pow(10, 18)


class LendingblockProxy(EthereumProxy):

    def get_method_hash(self, method):
        method_sig = self.get_method_signature(method)
        if method_sig:
            return '0x' + keccak(method_sig.encode()).hex()[:8]

    @classmethod
    def get_addr_hash(cls, addr):
        if addr.startswith('0x'):
            return addr.lower()[2:].zfill(64)
        return ''

    @classmethod
    def get_amount_hash(cls, num):
        return hex(int(num * DECIMALS))[2:].zfill(64)

    @classmethod
    def get_method_signature(cls, method):
        method_abi_list = [
            x for x in settings.LND_CONTRACT['abi'] if x.get('name') == method
        ]
        if not method_abi_list:
            return
        method_abi = method_abi_list[0]
        method_sig = method
        method_sig += '('
        inputs = method_abi.get('inputs')
        if inputs:
            for inp in inputs:
                method_sig += inp['type']
                if inp is not inputs[-1]:
                    method_sig += ','
        method_sig += ')'
        return method_sig

    async def call_contract_method(
        self,
        method,
        to_int=False,
        to_string=False,
    ):
        contract_address = settings.LND_CONTRACT_ADDR
        result = await self.post('eth_call', {
            'to': to_checksum_address(contract_address),
            'data': self.get_method_hash(method)
        }, 'latest')
        if to_int:
            return int(result, 16)
        elif to_string:
            return decode_abi(['string'], HexBytes(result))[0].decode()
        return result

    async def get_transaction_dict(self, priv, addr_to, amount, nonce):
        contract_address = settings.LND_CONTRACT_ADDR
        method_hash = self.get_method_hash('transfer')
        addr_hash = self.get_addr_hash(addr_to)
        amount_hash = self.get_amount_hash(amount)
        data = method_hash + addr_hash + amount_hash
        return {
            'from': Account.privateKeyToAccount(priv).address,
            'to': to_checksum_address(contract_address),
            'value': 0,
            'gas': 100000,
            'gasPrice': await self.get_gas_price(),
            'data': data,
            'chainId': int(settings.ETH_CHAIN_ID),
            'nonce': nonce
        }

    async def send_money(self, priv, addrs, validate=True):
        addr_from = Account.privateKeyToAccount(priv).address
        nonce = await self.get_transaction_count(addr_from)
        tx_ids = [
            await self.send_single_transaction(priv, addr, amount, nonce + i)
            for i, (addr, amount) in enumerate(addrs)
        ]
        return tx_ids

    async def get_lnd_balance(self, addr):
        method_hash = self.get_method_hash('balanceOf')
        addr_hash = self.get_addr_hash(addr)
        result = await self.post('eth_call', {
            'data': method_hash + addr_hash,
            'to': settings.LND_CONTRACT_ADDR,
        }, 'latest')
        return D(int(result, 16) / DECIMALS)

    @classmethod
    def validate_addr(cls, addr):
        if is_address(addr):
            return addr

    async def create_contract(self):
        tx_hash = await self.post('eth_sendTransaction', {
            'from': settings.MAIN_LND_ADDR,
            'gas': 4000000,
            'gasPrice': 100,
            'data': settings.LND_CONTRACT['bytecode'],
        })
        receipt = await self.post('eth_getTransactionReceipt', tx_hash)
        return receipt['contractAddress']

    async def create_wallet(self):
        account = Account().create()
        addr, priv = account.address, account.privateKey.hex()
        eth = EthereumProxy()
        await eth.send_money(settings.BUFFER_ETH_PRIV, [(addr, D('0.1'))])
        return addr, priv

    async def create_wallet_with_initial_balance(self):
        account = Account().create()
        addr = account.address
        priv = account.privateKey.hex()
        settings.LND_CONTRACT_ADDR = await self.create_contract()
        eth = EthereumProxy()
        await eth.send_money(settings.MAIN_LND_PRIV, [(addr, D(1000))])
        await self.send_money(settings.MAIN_LND_PRIV, [(addr, D(10000))])
        return addr, priv
