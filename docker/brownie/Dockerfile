FROM python:3.9-slim

ARG PUID=1000
ENV PUID ${PUID}
ARG PGID=1000
ENV PGID ${PGID}

COPY entrypoint.sh /app/

# Update package manager and install required dependencies
RUN apt-get update \
    && apt-get install -y build-essential tk

# Install brownie
RUN python3 -m pip install --upgrade pip && pip3 install eth-brownie==1.18.1

# Add non-root user
RUN groupadd -g ${PGID} brownie \
    && useradd -u ${PUID} -g brownie -m user \
    && usermod -p "*" user -s /bin/bash \
    && chown -R user:brownie /home/user

# Set default user
USER user

# Create directory for project
RUN mkdir /home/user/marketplace

# Set working directory
WORKDIR /home/user/marketplace

ENTRYPOINT ["bash", "/app/entrypoint.sh"]