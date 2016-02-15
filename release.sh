# Do a release. This is more a canned set of instructions than a script.

set -e -v

${VISUAL} xtas/_version.py
${VISUAL} doc/conf.py
${VISUAL} doc/changelog.rst
git add xtas/_version.py doc/conf.py doc/changelog.rst
git commit

git tag -a v$(python -c 'execfile("xtas/_version.py"); print(__version__)')
git push --tags

clonedir=$(mktemp -d)
git clone . "$clonedir"
cd "$clonedir"
python setup.py sdist upload

echo "To push new docs: (cd doc && make gh-pages && git push origin gh-pages)"
