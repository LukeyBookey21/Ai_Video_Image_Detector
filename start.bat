@echo off
echo ==========================================
echo   AI Detector - Starting...
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from python.org
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install from nodejs.org
    pause
    exit /b 1
)

:: Install backend deps if needed
if not exist "backend\__pycache__" (
    echo Installing backend dependencies...
    cd backend
    pip install -r requirements.txt
    cd ..
)

:: Install frontend deps if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

:: Start backend
echo Starting backend on http://localhost:8000...
start /B cmd /c "cd backend && python main.py"

:: Wait for backend
timeout /t 5 /nobreak >nul

:: Start frontend
echo Starting frontend on http://localhost:5173...
cd frontend
start /B cmd /c "npm run dev"
cd ..

:: Wait and open browser
timeout /t 3 /nobreak >nul
echo.
echo ==========================================
echo   App is running!
echo   Web UI:  http://localhost:5173
echo   API:     http://localhost:8000
echo   CLI:     python cli.py --help
echo ==========================================
echo.
echo Press any key to stop...
start http://localhost:5173
pause

:: Cleanup
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "python.exe" /fi "WINDOWTITLE eq *main.py*" >nul 2>&1
