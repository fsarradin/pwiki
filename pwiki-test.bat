@echo off
setlocal
set script_path=%~dp0
set src_path=%script_path%src
echo %src_path%
set PYTHONPATH=%PYTHONPATH%;%src_path%
python %src_path%\pwiki.py --port=8010 --db=%script_path%data\wiki-test.db --css=%script_path%css\wiki.css
