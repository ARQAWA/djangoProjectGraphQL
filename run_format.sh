#!/bin/bash
set -e
set -x
isort . --profile black
black . --target-version py311
