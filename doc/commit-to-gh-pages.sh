#! /bin/sh

# Hash the generated HTML docs and commit them to the branch gh-pages.
# Will not push them to GitHub.

set -e -v

treehash=$(${PYTHON:-python} hash-tree.py "${1:-_build/html}")
parent=$(git rev-parse gh-pages)

msg="Regenerated docs for $(git rev-parse HEAD)"
commithash=$(echo "$msg" | git commit-tree $treehash -p $parent)
echo "Updating gh-pages to $commithash"
git update-ref refs/heads/gh-pages "$commithash"
