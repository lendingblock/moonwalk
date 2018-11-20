from eth_keys.datatypes import PublicKey, PrivateKey
from eth_utils import to_wei

from . import main
from . import settings


def private_key_to_checksum_address(key):
    if key.startswith('0x'):
        key = key[2:]
    return PublicKey.from_private(
        PrivateKey(bytes.fromhex(key))
    ).to_checksum_address()


class EthHelperMixin:
    MAIN_ADDR = private_key_to_checksum_address(settings.BUFFER_ETH_PRIV)

    @classmethod
    def register(cls):
        pass


class EthHelper(EthHelperMixin, main.Ethereum):
    async def send_money(self, addr, amount):
        nonce = await self.post(
            'eth_getTransactionCount',
            self.MAIN_ADDR,
        )
        tx = {
            'from': self.MAIN_ADDR,
            'to': addr,
            'value': to_wei(amount, 'ether'),
            'gas': 22000,
            'gasPrice': to_wei(8, 'gwei'),
            'chainId': 1,
            'nonce': nonce,
        }
        return await self.post('eth_sendTransaction', tx)


class LndHelper(EthHelperMixin, main.Lendingblock):
    async def create_contract(self):
        tx_hash = await self.post('eth_sendTransaction', {
            'from': self.MAIN_ADDR,
            'gas': 4000000,
            'gasPrice': 100,
            'data': settings.LND_CONTRACT['bytecode'],
        })
        receipt = await self.post(
            'eth_getTransactionReceipt',
            tx_hash
        )
        return receipt['contractAddress']
