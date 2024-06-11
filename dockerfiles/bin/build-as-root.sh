#!/bin/bash

# installs system packages required for working with Janeway on a deb

# Enable unofficial Bash strict mode

set -euo pipefail

# uncommment this for debug
# set -x

apt update -qq
apt install -y aptitude
aptitude install -y python3-lxml \
     pylint \
     libxml2-dev \
     libxml2-utils \
     libxslt1-dev \
     python3-dev \
     zlib1g-dev \
     lib32z1-dev \
     libffi-dev \
     libssl-dev \
     libjpeg-dev