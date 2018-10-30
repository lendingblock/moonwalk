# Moonwalking


[![PyPI version](https://badge.fury.io/py/moonwalking.svg)](https://badge.fury.io/py/moonwalking)

[![CircleCI](https://circleci.com/gh/lendingblock/moonwalking.svg?style=svg)](https://circleci.com/gh/lendingblock/moonwalking)

[![codecov](https://codecov.io/gh/lendingblock/moonwalking/branch/master/graph/badge.svg)](https://codecov.io/gh/lendingblock/moonwalking)


Moonwalking is an open-source library that provides the following functionality:
  - creating wallets
  - validating addresses
  - checking balance
  - sending money by creating transactions


At the time Moonwalking supports the following cryptocurrencies:
  - Bitcoin (BTC)
  - Bitcoin Cash (BCH)
  - Litecoin (LTC)
  - Ethereum (ETH)
  - Lendingblock (LND)


In the future support for some other cryptocurrencies may be added if needed.

## Testing

For testing you need docker and docker-compose installed.
Launch the blockchain clients
```
make blockchains-remove
```
Create coins
```
make coins
```
and run tests
```
make tests
```
