@echo off
echo Starting Dilse.ai...
echo.
echo Make sure Redis and Ollama are running!
echo.
start "Celery Worker" cmd /k "celery -A tasks worker --loglevel=info -P solo"
start "Flask App" cmd /k "python app.py"
echo App and Worker started in new windows.
pause
