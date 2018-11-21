build2push: clean
	(python3.6 setup.py bdist_wheel)
	twine upload -r local dist/*

clean:
	rm -rf ${CURDIR}/build ${CURDIR}/dist ${CURDIR}/*.egg-info

test:
	python -m unittest discover -p "*_test.py"
