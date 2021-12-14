FROM python:3.7-alpine

ARG PUID=1000
ENV PUID ${PUID}
ARG PGID=1000
ENV PGID ${PGID}

# Update package manager and install required dependencies
RUN apk update \
    && apk upgrade \
    && apk add --no-cache bash gcc musl-dev linux-headers tk

# Install brownie
RUN python3 -m pip install --upgrade pip && pip install eth-brownie==1.17.2

# Add non-root user
RUN addgroup -g ${PGID} brownie \
    && adduser -D -u ${PUID} -s /bin/bash -h /home/user -G brownie user \
    && chown -R user:brownie /home/user

# Set default user
USER user

# Create directory for project
RUN mkdir /home/user/artion

# Set working directory
WORKDIR /home/user/artion

# Update default network host to point on ganache-cli container
RUN brownie networks modify development host=http://ganache-cli