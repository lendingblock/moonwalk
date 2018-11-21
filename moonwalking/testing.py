from eth_keys.datatypes import PrivateKey, PublicKey
from eth_utils import to_wei

from moonwalking.main import Ethereum
from . import settings


def private_key_to_checksum_address(key):
    if key.startswith('0x'):
        key = key[2:]
    return PublicKey.from_private(
        PrivateKey(bytes.fromhex(key))
    ).to_checksum_address()


ETH_MAIN_ADDR = private_key_to_checksum_address(settings.BUFFER_ETH_PRIV)
eth = Ethereum()


async def send_eth(addr, amount):
    nonce = await eth.post(
        'eth_getTransactionCount',
        ETH_MAIN_ADDR,
    )
    tx = {
        'from': ETH_MAIN_ADDR,
        'to': addr,
        'value': to_wei(amount, 'ether'),
        'gas': 22000,
        'gasPrice': to_wei(8, 'gwei'),
        'chainId': 1,
        'nonce': nonce,
    }
    return await eth.post('eth_sendTransaction', tx)


async def create_lnd_contract():
    tx_hash = await eth.post('eth_sendTransaction', {
        'from': ETH_MAIN_ADDR,
        'gas': 4000000,
        'gasPrice': 100,
        'data': settings.LND_CONTRACT['bytecode'],
    })
    receipt = await eth.post(
        'eth_getTransactionReceipt',
        tx_hash
    )
    return receipt['contractAddress']
