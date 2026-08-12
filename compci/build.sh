#!/usr/bin/env bash
set -e

if [ $# -ne 1 ]; then
    echo "uso: $0 arquivo.ci"
    exit 1
fi

# compila (.ci -> .s), monta (.s -> .o), linka (.o -> executavel) e executa.
# O assembly gerado usa .include "runtime.s", entao o montador precisa rodar
# com runtime.s alcancavel a partir do diretorio de trabalho.
entrada="$1"
base="${entrada%.ci}"

python3 compci.py "$entrada"
as --64 -o "$base.o" "$base.s"
ld -o "$base" "$base.o"
"./$base"
