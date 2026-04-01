@echo off
setlocal
pushd "%~dp0"
if exist ".venv\Scripts\python.exe" (
	.venv\Scripts\python.exe src\nsm_debug_mcp\server.py %*
) else (
	py -3 src\nsm_debug_mcp\server.py %*
)
popd
endlocal