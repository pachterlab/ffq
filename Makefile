.PHONY : install test check build docs clean push_release

test:
	nosetests --verbose --with-coverage --cover-package ffq

check:
	flake8 ffq && echo OK
	yapf -r --diff ffq && echo OK

build:f
	python setup.py sdist bdist_wheel

docs:
	sphinx-build -a docs docs/_build

clean:
	rm -rf build
	rm -rf dist
	rm -rf ffq.egg-info
	rm -rf docs/_build
	rm -rf docs/api

bump_patch:
	bumpversion patch

bump_minor:
	bumpversion minor

bump_major:
	bumpversion major

push_release:
	git push && git push --tags
