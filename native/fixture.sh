#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ "$1" != "--probe" ]; then
  echo "usage: npm-actions-native-fixture --probe" >&2
  exit 64
fi

printf '%s\n' 'npm-actions-native-fixture-ok'
