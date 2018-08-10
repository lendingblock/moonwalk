
.PHONY: help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

clean:		## remove python cache files
	find . -name '__pycache__' | xargs rm -rf
	find . -name '*.pyc' -delete
	rm -rf build

test:		## Run flake8 & unit tests
	flake8
	export PYTHON_ENV=test && pytest --cov

version:	## Display version
	@python3 -c "import moonwalk; print(moonwalk.__version__)"

codecov:	## Upoload coverage report to codecov
	codecov --token $(CODECOV_TOKEN)
