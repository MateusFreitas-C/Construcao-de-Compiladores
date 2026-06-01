FROM python:3.12-slim

RUN pip install --no-cache-dir cram

WORKDIR /compci
COPY . /compci

RUN chmod +x build.sh

# por padrao roda a suite de testes do analisador lexico
CMD ["cram", "tests/lexer.t"]
