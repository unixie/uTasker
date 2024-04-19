#!/bin/zsh
set -e

echo Installing Python requirements into .venv
if [ -d .venv ]; then
    echo .venv already exists, exiting
    exit
fi

if [[ "$OSTYPE" == "msys" ]]
then
    echo MSYS detected, using Windows paths
    ACTIVATE_PATH=Scripts
else
    echo Unix-like detected
    ACTIVATE_PATH=bin
fi

python3 -m venv --clear --upgrade-deps .venv
source .venv/$ACTIVATE_PATH/activate
pip install -r requirements.txt --require-virtualenv --prefer-binary

SITE_PACKAGES_PATH=$(find .venv -iname "site-packages")
echo $PWD/lib > $SITE_PACKAGES_PATH/here.pth

echo Done!
