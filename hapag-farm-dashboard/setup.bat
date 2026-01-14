@echo off
echo Setting up Hapag Farm Dashboard...
echo.

echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo To run the dashboard:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Run Streamlit: streamlit run app.py
echo.
pause