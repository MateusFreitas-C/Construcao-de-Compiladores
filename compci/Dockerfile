FROM python:3.12-slim

# binutils fornece 'as' e 'ld', usados pelos testes end-to-end (build.sh)
RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir cram

WORKDIR /compci
COPY . /compci

RUN chmod +x build.sh

# por padrao roda a suite completa de testes do compilador Fun
CMD ["cram", "tests/lexer.t", "tests/parser.t", "tests/semantic.t", "tests/codegen.t", "tests/funcoes.t"]
