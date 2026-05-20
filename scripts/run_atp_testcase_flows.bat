@echo off
setlocal EnableExtensions
REM ATP TestCase Flows runner (recursive yaml/yml). Does not replace Printing / Non-printing runners.
REM Args: APP_PACKAGE CLEAR_STATE MAESTRO_CMD [ATP_SUBFOLDER]
REM       Optional 4th arg: Jenkins legacy name or HP500 folder (e.g. SignUp_Login, signup-login).

set "RR=%~dp0.."
for %%I in ("%RR%") do set "RR=%%~fI"

cd /d "%RR%"
set "ATP_SUB=%~4"
if not "%~4"=="" (
  for /f "usebackq delims=" %%F in (`python "%~dp0atp_folder_resolve.py" "%~4" "%RR%"`) do set "ATP_SUB=%%F"
)
if "%ATP_SUB%"=="" (
  python -m execution.atp_jenkins_orchestrator "%RR%" "%~1" "%~2" "%~3" ""
) else (
  python -m execution.atp_jenkins_orchestrator "%RR%" "%~1" "%~2" "%~3" "%ATP_SUB%"
)
set "EC=%ERRORLEVEL%"
endlocal
exit /b %EC%
