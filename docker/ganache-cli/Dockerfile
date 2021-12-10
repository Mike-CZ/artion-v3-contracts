FROM trufflesuite/ganache-cli:v6.12.2

COPY entrypoint.sh /app/

RUN apk update \
    && apk upgrade \
    && apk add --no-cache bash

ENTRYPOINT ["bash", "entrypoint.sh"]