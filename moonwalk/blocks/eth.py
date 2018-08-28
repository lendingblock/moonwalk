from decimal import Decimal as D

from aiohttp.client import ClientSession
from eth_account.account import Account
from eth_utils.address import is_address
from eth_utils.currency import to_wei, from_wei

from .. import settings
from .base import EthereumError, NotEnoughAmountError,\
    ReplacementTransactionError, BaseProxy


class EthereumProxy(BaseProxy):

    MAX_FEE = 100
    URL = settings.ETH_URL
    FEE_URL = 'https://ethgasstation.info/json/ethgasAPI.json'
    NETWORK = 'testnet' if settings.USE_TESTNET else 'mainnet'

    def get_data(self, method, *params):
        return {
            'jsonrpc': '2.0',
            'method': method,
            'params': list(params),
            'id': self.NETWORK
        }

    async def post(self, *args):
        async with ClientSession() as session:
            async with session.post(
                self.URL,
                json=self.get_data(*args),
            ) as res:
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
            async with ClientSession() as session:
                async with session.get(self.FEE_URL) as res:
                    resp_dict = await res.json()
                    average = int(resp_dict['average'] / 10)
                    return to_wei(
                        int(min(self.MAX_FEE, average)),
                        'gwei',
                    )
        return to_wei(int(settings.ETH_FEE), 'gwei')

    async def get_balance(self, addr):
        balance = await self.post('eth_getBalance', addr, 'latest')
        return D(from_wei(int(balance, 16), 'ether'))

    async def send_single_transaction(
        self,
        priv,
        addr_to,
        amount,
        nonce,
        max_attempts=10,
    ):
        if max_attempts < 1:
            return
        tx_dict = await self.get_transaction_dict(
            priv,
            addr_to,
            amount,
            nonce,
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
                max_attempts=max_attempts
            )

    async def get_transaction_dict(self, priv, addr_to, amount, nonce):
        gas = 21000
        get_code = await self.post('eth_getCode', addr_to, 'latest')
        if len(get_code) > 3:
            gas = 50000
        gas_price = await self.get_gas_price()
        fee = gas * gas_price
        value = to_wei(amount, 'ether') - fee
        return {
            'from': Account.privateKeyToAccount(priv).address,
            'to': addr_to,
            'value': value,
            'gas': gas,
            'gasPrice': gas_price,
            'chainId': int(settings.ETH_CHAIN_ID),
            'nonce': nonce,
        }

    async def validate_balance(self, priv, addrs):
        addr_from = Account.privateKeyToAccount(priv).address
        balance = await self.get_balance(addr_from)
        addr, amount = addrs[0]
        if amount > balance:
            raise NotEnoughAmountError()

    async def get_transaction_count(self, addr_from):
        nonce = await self.post(
            'eth_getTransactionCount',
            addr_from,
            'pending',
        )
        return int(nonce, 16)

    async def send_money(self, priv, addrs):
        await self.validate_balance(priv, addrs)
        addr_from = Account.privateKeyToAccount(priv).address
        nonce = await self.get_transaction_count(addr_from)
        tx_ids = [
            await self.send_single_transaction(priv, addr, amount, nonce + i)
            for i, (addr, amount) in enumerate(addrs)
        ]
        return tx_ids

    async def send_all_eth_to_buffer_wallet(self, priv):
        addr = Account.privateKeyToAccount(priv).address
        buffer_addr = Account.privateKeyToAccount(
            settings.BUFFER_ETH_PRIV
        ).address
        balance = await self.get_balance(addr)
        return await self.send_money(priv, [(buffer_addr, balance)])

    @classmethod
    def validate_addr(cls, addr):
        if is_address(addr):
            return addr

    async def create_wallet(self):
        account = Account().create()
        return account.address, account.privateKey.hex()

    async def create_wallet_with_initial_balance(self):
        account = Account().create()
        addr = account.address
        priv = account.privateKey.hex()
        await self.send_money(settings.BUFFER_ETH_PRIV, [(addr, D(100))])
        return addr, priv
