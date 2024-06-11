#!/bin/bash

# bootstraps the Janeway development environment

# Enable unofficial Bash strict mode

set -euo pipefail

# uncommment this for debug
# set -x

cd /app && pip3 install --upgrade pip && \
           pip3 install mysqlclient==2.0.1 psycopg2-binary~=2.8.0 && \
           pip3 install Cython && \
           pip3 install -r requirements.txt && \
           pip3 install -r dev-requirements.txt && \
           pip3 install xmltodict gitpython faker
