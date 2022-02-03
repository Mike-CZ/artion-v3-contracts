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

### Project setup
Before running containers, run script `setup.sh` on your machine.

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

### Intellij package discovery
To be able to navigate through packages (OpenZeppelin) files, you have to first connect to brownie container and build project.
All packages will be automatically downloaded. Then disconnect from container and run script `ide_helper.sh` on your machine.

### macOS X11 forwarding
To make brownie gui work, install [xquartz](https://gist.github.com/cschiewek/246a244ba23da8b9f0e7b11a68bf3285)