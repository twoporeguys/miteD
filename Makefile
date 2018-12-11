.PHONY: build2push clean deps test

build2push: clean
	(python3.6 setup.py bdist_wheel)
	twine upload -r local dist/*

clean:
	rm -rf ${CURDIR}/build ${CURDIR}/dist ${CURDIR}/*.egg-info

venv:
	virtualenv venv

deps: venv
	./venv/bin/pip install -r requirements.txt

test: deps
	./venv/bin/coverage run --branch -m unittest discover -p "*_test.py"
	./venv/bin/coverage xml
	./venv/bin/coverage report -m
	./venv/bin/coverage erase
