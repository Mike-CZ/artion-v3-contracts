#!/bin/bash

## Create symlink for intellij to be able to find package files
## See more: https://github.com/intellij-solidity/intellij-solidity/issues/246

SCRIPTS_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
DOCKER_DIR=$(dirname "$SCRIPTS_DIR")
ROOT_DIR=$(dirname "$DOCKER_DIR")

# read open zeppelin version from config file
OPEN_ZEPPELIN_VERSION=$(sed -n -e 's/^.*OpenZeppelin\/openzeppelin-contracts@//p' $ROOT_DIR/brownie-config.yml | head -1 | xargs)

NODE_MODULES_PATH="$ROOT_DIR/node_modules";
if [[ ! -d ${NODE_MODULES_PATH} ]]; then
  echo "Creating node_modules directory: ${NODE_MODULES_PATH}";
  mkdir ${NODE_MODULES_PATH};
fi

OPEN_ZEPPELIN_DATA_PATH="$DOCKER_DIR/.data/brownie/packages/OpenZeppelin"

create_symlink()
{
  if [[ ! -d $1 ]]; then
    echo "Package source path not found in $1";
    return
  fi

  ln -f -s $1 "$NODE_MODULES_PATH/$2"
  echo "Created symlink for $2"
}

create_symlink "$OPEN_ZEPPELIN_DATA_PATH/openzeppelin-contracts@$OPEN_ZEPPELIN_VERSION" "openzeppelin"
create_symlink "$OPEN_ZEPPELIN_DATA_PATH/openzeppelin-contracts-upgradeable@$OPEN_ZEPPELIN_VERSION" "openzeppelin-upgradeable"