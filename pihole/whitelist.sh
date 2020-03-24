#!/usr/bin/with-contenv bash

# Grabs an up-to-date whitelist from anudeepND/whitelist
# Run on container-start

git clone https://github.com/anudeepND/whitelist.git
./whitelist/scripts/whitelist.sh
rm -rf whitelist
