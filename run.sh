#!/bin/bash
CURRENT=$(cd $(dirname $0);pwd)
cd $CURRENT
source .venv/bin/activate
uv pip install .
server_menu
