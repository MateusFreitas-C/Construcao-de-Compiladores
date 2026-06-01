set -e

if [ $# -ne 1 ]; then
    echo "uso: $0 arquivo.ci"
    exit 1
fi

ci="$1"
base="${ci%.ci}"

python3 compci.py "$ci"
as --64 -o "$base.o" "$base.s"
ld -o "$base" "$base.o"

echo "--- saida do programa ---"
"./$base"