#!/bin/bash

SCRIPTS_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
ROOT_DIR=$(dirname "$SCRIPTS_DIR")

DATA_PATH="$ROOT_DIR/.data";
if [[ ! -d ${DATA_PATH} ]]; then
    echo "Creating data directory: ${DATA_PATH}";
    mkdir ${DATA_PATH};
fi

BROWNIE_DATA_PATH="$DATA_PATH/brownie";
if [[ ! -d ${BROWNIE_DATA_PATH} ]]; then
    echo "Creating brownie data directory: ${BROWNIE_DATA_PATH}";
    mkdir ${BROWNIE_DATA_PATH};
fi

SOLC_DATA_PATH="$DATA_PATH/solc";
if [[ ! -d ${SOLC_DATA_PATH} ]]; then
    echo "Creating solc data directory: ${SOLC_DATA_PATH}";
    mkdir ${SOLC_DATA_PATH};
fi

SOLCX_DATA_PATH="$DATA_PATH/solcx";
if [[ ! -d ${SOLCX_DATA_PATH} ]]; then
    echo "Creating solcx data directory: ${SOLCX_DATA_PATH}";
    mkdir ${SOLCX_DATA_PATH};
fi