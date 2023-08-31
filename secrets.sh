#!/bin/bash

random_md5=$(openssl rand -hex 16)
echo "TOKEN=$random_md5" > secrets_tmp.sh
cp secrets_tmp.sh controller/secrets.sh
mv secrets_tmp.sh sloth/secrets.sh