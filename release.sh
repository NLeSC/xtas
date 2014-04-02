set -e
${VISUAL} xtas/_version.py
${VISUAL} doc/conf.py
git tag -a v$(python -c 'execfile("xtas/_version.py"); print(__version__)')
git push --tags
clonedir=$(mktemp -d)
git clone . "$clonedir"
cd "$clonedir"
python setup.py sdist upload
