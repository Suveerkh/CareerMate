@echo off
echo Setting up CareerMate Desktop Application...

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Node.js is not installed. Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo npm is not installed. Please install npm (it usually comes with Node.js)
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
call npm install

REM Copy the logo to the icons directory
echo Creating application icons...
if not exist icons mkdir icons
copy /Y "..\static\images\career_mate - logo.png" "icons\icon.png"

echo Setup complete! You can now run the application with 'npm start'