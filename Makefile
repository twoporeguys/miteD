DOCKER :=/usr/local/bin/docker
DOCKER_COMPOSE :=/usr/local/bin/docker-compose

.PHONY: all tests clean

all:: tests

build2push: clean
	(python3.6 setup.py bdist_wheel)
	twine upload -r local dist/*

clean:
	rm -rf ${CURDIR}/build ${CURDIR}/dist ${CURDIR}/*.egg-info

tests:
	${DOCKER_COMPOSE} up --build --abort-on-container-exit --exit-code-from mited || exit 1
