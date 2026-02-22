@echo off
:: Script to read GIT_USERNAME or GIT_PASSWORD from environment variables

:: Check if an argument is provided
if "%~1"=="" (
    echo "Usage: %~nx0 [Username|Password]"
    exit /b 1
)

:: Convert the argument to lowercase for comparison
set "param=%~1"
set "param_lower=%param:~0,1%%param:~1%"

:: Check if the argument contains "username"
echo %param_lower% | findstr /i "username" >nul
if %errorlevel% equ 0 (
    echo %GIT_USERNAME%
    exit /b 0
)

:: Check if the argument contains "password"
echo %param_lower% | findstr /i "password" >nul
if %errorlevel% equ 0 (
    echo %GIT_PASSWORD%
    exit /b 0
)

:: If none of the cases are found
exit /b 1
