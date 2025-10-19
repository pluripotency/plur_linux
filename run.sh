#!/bin/bash
CURRENT=$(cd $(dirname $0);pwd)
cd $CURRENT
uv run server_menu
