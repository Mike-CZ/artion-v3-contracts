#!/bin/bash

# Update default network host to point on ganache-cli container
brownie networks modify development host=http://ganache-cli

# make sure container is always up
tail -f /dev/null