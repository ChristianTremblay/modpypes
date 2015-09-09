#!/bin/bash

# remove everything in the current dist/ directory
[ -d dist ] && rm -Rfv dist

for ver in 2.7 3.4; do
    python$ver setup.py bdist_egg
    python$ver setup.py bdist_wheel
done

read -p "Upload to PyPI? [y/n/x] " yesno || exit 1

if [ "$yesno" = "y" ] ;
then
    twine upload dist/*
elif [ "$yesno" = "n" ] ;
then
    echo "Skipped..."
else
    echo "exit..."
    exit 1
fi

