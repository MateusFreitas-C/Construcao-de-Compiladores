set -e

if [ $# -ne 1 ]; then
    echo "uso: $0 arquivo.ci"
    exit 1
fi

python3 compci.py "$1"
