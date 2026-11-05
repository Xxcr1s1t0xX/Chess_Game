@echo off
cd /d "%~dp0"
py chess_game.py
if errorlevel 1 (
  echo.
  echo Python or Tkinter could not start the game.
  pause
)
