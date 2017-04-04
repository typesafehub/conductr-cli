echo off
SETLOCAL

set PACKAGE_VERSION_NUMBER=%1

if [%PACKAGE_VERSION_NUMBER%] == [] (
    echo "ERROR: Package version number must be specified"
    goto EndWithError
)

del /q dist\*

set PACKAGE_OS_NAME=Win32
set PACKAGE_NAME=conductr-cli-%PACKAGE_VERSION_NUMBER%-%PACKAGE_OS_NAME%.zip

echo.
echo Building %PACKAGE_NAME%
echo.

echo ------------------------------------------------
echo Creating single executable for 'conduct' command
echo ------------------------------------------------
echo.
pyinstaller --onefile conductr_cli/conduct.py

echo ------------------------------------------------
echo Creating single executable for 'shazar' command
echo ------------------------------------------------
echo.
pyinstaller --onefile conductr_cli/shazar.py

echo ------------------------------------------------
echo Creating single executable for 'bndl' command
echo ------------------------------------------------
echo.
pyinstaller --onefile conductr_cli/bndl.py

echo ------------------------------------------------
echo Validating version for 'conduct' command
echo ------------------------------------------------
echo.
del c:\temp\conduct-version.txt
conduct version > c:\temp\conduct-version.txt
set /p CONDUCT_VERSION=< c:\temp\conduct-version.txt

if %CONDUCT_VERSION% NEQ %PACKAGE_VERSION_NUMBER% (
    echo ERROR: Mismatched version number for 'conduct' command
    echo ERROR: 'conduct' command version: %CONDUCT_VERSION%
    echo ERROR: Package version: %PACKAGE_VERSION_NUMBER%
    goto EndWithError
)

echo ------------------------------------------------
echo Checking 'conduct' command is working as expected
echo ------------------------------------------------
echo.
conduct info

echo ------------------------------------------------
echo Checking 'shazar' command is working as expected
echo ------------------------------------------------
echo.
shazar -h

echo ------------------------------------------------
echo Checking 'bndl' command is working as expected
echo ------------------------------------------------
echo.
bndl -h


echo ------------------------------------------------
echo Building zip archive for %PACKAGE_NAME%
echo ------------------------------------------------
echo.
cd dist
7z a %PACKAGE_NAME% conduct.exe shazar.exe bndl.exe
cd ..

echo ------------------------------------------------
echo Success
echo ------------------------------------------------
echo Created archive in dist/%PACKAGE_NAME%
echo.
echo.

:EndWithError
echo.
