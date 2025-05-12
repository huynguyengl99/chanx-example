#!/usr/bin/env bash

if [ "$1" == "--fix" ]; then
  ruff check . --fix && black ./chanx_example && toml-sort ./*.toml
else
  ruff check . && black ./chanx_example --check && toml-sort ./*.toml --check
fi
