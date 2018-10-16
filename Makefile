
.PHONY: help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

clean:			## remove python cache files
	find . -name '__pycache__' | xargs rm -rf
	find . -name '*.pyc' -delete
	rm -rf build

blockchains:		## Starts blockchain clients in daemon mode
	docker-compose up -d

blockchains-remove:	## Starts blockchain clients and remove orphans
	docker-compose up --remove-orphans

coins:			## Generate Coins
	docker-compose exec -T bitcoin bitcoin-cli -rpcport=18443 -rpcuser=test -rpcpassword=test generate 150
	docker-compose exec -T litecoin litecoin-cli -rpcport=19332 -rpcuser=test -rpcpassword=test generate 150
	docker-compose exec -T bitcoin-cash bitcoin-cli -rpcport=18332 -rpcuser=test -rpcpassword=test generate 150

test:			## Run flake8 & unit tests
	flake8
	export PYTHON_ENV=test && pytest --cov

version:		## Display version
	@python3 -c "import moonwalk; print(moonwalk.__version__)"

codecov:		## Upoload coverage report to codecov
	codecov --token $(CODECOV_TOKEN)
