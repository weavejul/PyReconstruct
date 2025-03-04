#!/usr/bin/env bash

DIR=$( cd -- "$( dirname -- "$(readlink -f "${BASH_SOURCE[0]}" || ${BASH_SOURCE[0]})" )" &> /dev/null && pwd )

# Get correct python command
if python --version 2>&1 | grep -q '^Python 3.11'; then
    PY_CMD=python
else
    PY_CMD=Python3.11
fi

cd $DIR/../..

if [ ! -f "env/bin/activate" ]; then
    $PY_CMD -m venv env
    source env/bin/activate
    pip install --upgrade pip
    deactivate
fi

source env/bin/activate
pip install -r requirements.txt
python PyReconstruct/run.py
