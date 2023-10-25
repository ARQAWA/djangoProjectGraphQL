#!/bin/bash
set -e
set -x
#autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --ignore-init-module-imports .
isort . --profile black
black . --target-version py311
mypy . --python-version 3.11 --ignore-missing-imports --strict
