build2push:
	python3.6 setup.py bdist_wheel
	twine upload -r local dist/*

