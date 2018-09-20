import logging
from decimal import Decimal as D

from hexbytes.main import HexBytes
from eth_abi.abi import decode_abi
from eth_hash.auto import keccak
from eth_account import Account
from eth_utils import from_wei, to_checksum_address, is_address

from moonwalk import settings
from moonwalk.utils import GeneralError
from .exc import NotEnoughAmountError
from .eth import EthereumProxy


logger = logging.getLogger(__name__)
DECIMALS = pow(10, 18)


class LendingblockProxy(EthereumProxy):
    MAX_GAS = 100000
    LND_WALLETS_TOPUP_TRANS_NO = int(settings.LND_WALLETS_TOPUP_TRANS_NO)

    @staticmethod
    def get_contract_addr():
        """
        to make tests mocking easier
        """
        return settings.LND_CONTRACT_ADDR

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
    def get_method_signature(method):
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

    async def call_contract_method(self, method, to_int=False, to_string=False):
        contract_address = self.get_contract_addr()
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
        contract_address = self.get_contract_addr()
        method_hash = self.get_method_hash('transfer')
        addr_hash = self.get_addr_hash(addr_to)
        amount_hash = self.get_amount_hash(amount)
        data = method_hash + addr_hash + amount_hash
        return {
            'from': Account.privateKeyToAccount(priv).address,
            'to': to_checksum_address(contract_address),
            'value': 0,
            'gas': self.MAX_GAS,
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
            'to': self.get_contract_addr(),
        }, 'latest')
        return D(int(result, 16) / DECIMALS)

    @staticmethod
    def validate_addr(addr):
        if is_address(addr):
            return addr

    async def create_wallet(self):
        account = Account().create()
        addr, priv = account.address, account.privateKey.hex()
        eth = EthereumProxy()
        price = await eth.get_gas_price()
        single_tx_price = price * self.MAX_GAS
        single_tx_price = from_wei(single_tx_price, 'ether')
        try:
            await eth.send_money(
                settings.BUFFER_ETH_PRIV,
                [(addr, single_tx_price * self.LND_WALLETS_TOPUP_TRANS_NO)],
            )
        except NotEnoughAmountError:
            logger.error("not enough eth in buffer wallet")
            raise GeneralError("not enough eth in buffer wallet")

        return addr, priv
