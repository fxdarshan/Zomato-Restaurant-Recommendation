@echo off
echo =======================================================
echo Starting Zomato AI Restaurant Recommendation Engine...
echo =======================================================

echo Starting FastAPI Backend on Port 8000...
start "FastAPI Backend" cmd /k ".\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Streamlit Web UI on Port 8501...
start "Streamlit UI" cmd /k ".\.venv\Scripts\streamlit.exe run ui/app.py --server.port 8501"

echo =======================================================
echo Both services started!
echo - Streamlit UI: http://localhost:8501
echo - FastAPI Backend: http://localhost:8000
echo - API Docs (Swagger): http://localhost:8000/docs
echo =======================================================
