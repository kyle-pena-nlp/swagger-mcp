@echo off
echo Checking if uv is installed...

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo uv is not installed. Installing uv...
    pip install uv
)

echo Creating virtual environment using uv...
uv venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies using uv...
uv pip install -r requirements.txt

echo Setup complete! You can now run the API with: python run.py
pause 