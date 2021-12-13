# Setup guide

First, make sure to have [Docker](https://docs.docker.com/get-started/) (>=20.04) 
and [Docker Compose](https://docs.docker.com/compose/install/) (>=1.29.2) installed.

### Create .env file inside docker directory
```bash
cp .env.example .env
```

### Build images
```bash
docker-compose build --no-cache
```

### Run containers
```bash
docker-compose up -d
```
By default, port `8545` will be open on your computer. If you need to change it or change other parameters at startup, 
you can do so in the `.env` file.

### Connect to brownie container
```bash
docker-compose exec brownie bash
```