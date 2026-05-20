@echo off
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%export_atp.py" || exit /b 1
python "%SCRIPT_DIR%generate_maestro_project.py" || exit /b 1
echo Done: JSON/CSV updated and flows\signup-login\SL_*.yaml regenerated.
