#!/bin/bash

set -e

CURRENT_DIR=`pwd`
PACKAGE_VERSION_NUMBER="$1"

if [ -z "$PACKAGE_VERSION_NUMBER" ]; then
    echo "ERROR: Package version number must be specified"
    exit 1
fi

UNAME_VALUE=`uname`

if [ "$UNAME_VALUE" = "Darwin" ]; then
    PACKAGE_OS_NAME="Mac_OS_X-x86_64"
elif [ "$UNAME_VALUE" = "Linux" ]; then
    PACKAGE_OS_NAME="Linux-amd64"
else
    echo "ERROR: Unable to build package for $UNAME_VALUE"
    exit 1
fi

PACKAGE_NAME="conductr-cli-$PACKAGE_VERSION_NUMBER-$PACKAGE_OS_NAME.zip"

echo ""
echo "Building $PACKAGE_NAME"
echo ""

rm -f dist/*

echo "------------------------------------------------"
echo "Creating single executable for 'conduct' command"
echo "------------------------------------------------"
echo ""
pyinstaller --onefile conductr_cli/conduct.py

echo "------------------------------------------------"
echo "Creating single executable for 'shazar' command"
echo "------------------------------------------------"
echo ""
pyinstaller --onefile conductr_cli/shazar.py

echo "------------------------------------------------"
echo "Creating single executable for 'sandbox' command"
echo "------------------------------------------------"
echo ""
pyinstaller --hidden-import psutil --onefile conductr_cli/sandbox.py


echo "------------------------------------------------"
echo "Validating version for 'conduct' command"
echo "------------------------------------------------"
echo ""
# Do not use `head -n 1` to trim the first line of the output as this will result in broken pipe error in Linux.
CONDUCT_VERSION=$(dist/conduct version)
CONDUCT_VERSION=$(echo $CONDUCT_VERSION | awk '{print $1}')

if [ "$CONDUCT_VERSION" != "$PACKAGE_VERSION_NUMBER" ]; then
    echo "ERROR: Mismatched version number for 'conduct' command"
    echo "ERROR: 'conduct' command version: $CONDUCT_VERSION"
    echo "ERROR: Package version: $PACKAGE_VERSION_NUMBER"
    exit 1
fi

echo "------------------------------------------------"
echo "Validating version for 'sandbox' command"
echo "------------------------------------------------"
echo ""
# Do not use `head -n 1` to trim the first line of the output as this will result in broken pipe error in Linux.
SANDBOX_VERSION=$(dist/sandbox version)
SANDBOX_VERSION=$(echo $SANDBOX_VERSION | awk '{print $1}')

if [ "$SANDBOX_VERSION" != "$PACKAGE_VERSION_NUMBER" ]; then
    echo "ERROR: Mismatched version number for 'sandbox' command"
    echo "ERROR: 'sandbox' command version: $SANDBOX_VERSION"
    echo "ERROR: Package version: $PACKAGE_VERSION_NUMBER"
    exit 1
fi

echo "------------------------------------------------"
echo "Checking 'sandbox' and 'conduct' command is working as expected"
echo "------------------------------------------------"
echo ""

dist/sandbox run 2.0.0 -f visualization
echo "Checking Visualizer"
curl http://192.168.10.1:9008/services/visualizer
echo ""
conduct info
dist/sandbox stop

echo "------------------------------------------------"
echo "Checking 'shazar' command is working as expected"
echo "------------------------------------------------"
echo ""

dist/shazar -h

echo "------------------------------------------------"
echo "Building zip archive for $PACKAGE_NAME"
echo "------------------------------------------------"
echo ""
zip -j dist/$PACKAGE_NAME dist/conduct dist/sandbox dist/shazar

echo "------------------------------------------------"
echo "Success"
echo "------------------------------------------------"
echo "Created archive in dist/$PACKAGE_NAME"
echo ""
echo ""

