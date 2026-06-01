# Compilador CI

Compilador para a linguagem CI (Constantes Inteiras). Um programa CI
é uma constante inteira; o compilador gera assembly x86-64 (sintaxe
GNU Assembler, Linux) que imprime essa constante.

## Uso com Docker

Construir a imagem (só uma vez, ou sempre que mudar o codigo):

```
docker build -t compci .
```

Rodar o teste padrao (compila `tests/ok.ci`, monta, linka e executa):

```
docker run --rm compci
```


Saida esperada:

```
gerado: tests/ok.s
--- saida do programa ---
42
```

### Testar o caso de erro

```
docker run --rm compci bash ./build.sh tests/erro.ci
```

O `build.sh` para no primeiro erro: o `compci.py` falha, o `as` e o
`ld` nao chegam a rodar, e o container sai com codigo != 0.

### Abrir um shell no container (pra explorar)

```
docker run --rm -it --entrypoint bash compci
```

Lá dentro voce pode rodar manualmente:

```
python3 compci.py tests/ok.ci
as --64 -o tests/ok.o tests/ok.s
ld -o tests/ok tests/ok.o
./tests/ok
```
