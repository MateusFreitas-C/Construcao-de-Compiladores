FROM python:3.12-slim

# binutils traz `as` (assembler) e `ld` (linker)
RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /compci
COPY . /compci

# build.sh faz tudo: compci.py -> as -> ld -> executa
RUN chmod +x build.sh

# por padrao roda o teste tests/ok.ci; sobrescreva com:
#   docker run --rm compci ./build.sh outro.ci
CMD ["bash", "build.sh", "tests/ok.ci"]