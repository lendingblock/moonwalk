from datetime import datetime, timedelta

from aiohttp import ClientSession

from eth_utils.currency import to_wei

from .. import settings


class FeeStation:

    FEE_CACHES = {}
    BITCOIN_FEE_URL = 'https://bitcoinfees.earn.com/api/v1/fees/recommended'
    ETH_GAS_PRICE_URL = 'https://ethgasstation.info/json/ethgasAPI.json'

    def __init__(self, currency):
        self.currency = currency.lower()

    async def get_fee(self):
        fee, dt = self.FEE_CACHES.get(self.currency, (None, None))
        valid_till = datetime.utcnow() - timedelta(
            minutes=int(settings.FEE_CACHE_TIME)
        )
        if not fee or dt < valid_till:
            method = f'get_{self.currency}_fee'
            value = await getattr(self, method)()
            self.FEE_CACHES[self.currency] = (value, datetime.utcnow())
            return value
        return fee

    @staticmethod
    async def get(url):
        async with ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def get_btc_fee(self):
        resp_dict = await self.get(self.BITCOIN_FEE_URL)
        fatest_fee = int(resp_dict['fastestFee'])
        return fatest_fee

    async def get_eth_fee(self):
        resp_dict = await self.get(self.ETH_GAS_PRICE_URL)
        average = int(resp_dict['average'] / 10)
        return to_wei(average, 'gwei')
