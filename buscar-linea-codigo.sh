#! /bin/bash

git ls-files | grep '\.py$' | xargs grep $1
