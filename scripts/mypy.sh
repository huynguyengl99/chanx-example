#!/usr/bin/env bash

set -e

export PYTHONPATH=":chanx_example"


# Cleaning existing cache:
if [ "$1" == "-nc" ]; then
  rm -rf .mypy_cache
fi


mypy chanx_example
