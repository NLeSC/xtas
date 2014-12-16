# Ad hoc shell script to install Frog.
# Because this is so brittle, and Frog is so heavy on dependencies, no attempt
# is made to install Frog from within xtas like we do with Stanford NER.
#
# To install dependencies on Debian, issue:
#
#   apt-get install gawk libbz2-dev libtar-dev libboost-regex-dev pkg-config
#   apt-get install libreadline-dev

MAKE=${MAKE:-make}
MAKEOPT=${MAKEOPT:-}

prefix=$1
if [ "$prefix" = "" ]; then
    echo "usage: $0 PREFIX" >&2
    echo "    to install into directory PREFIX" >&2
    exit 1
fi

set -e -x

tmp=$(mktemp -d)
cd $tmp

PACKAGES="ticcutils libfolia ucto timbl mbt timblserver frog frogdata"

for pkg in $PACKAGES; do
    tarball="${pkg}-latest.tar.gz"
    wget "http://software.ticc.uvt.nl/${tarball}"
    srcdir=$(tar tzf "${tarball}" | head -1)
    tar xzf "${tarball}"
    cd "${srcdir}"
    ./configure --prefix=${prefix} && make ${MAKEOPT} && make install
done
