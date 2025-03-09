@echo off
setlocal

:: Check if config.yaml exists
if not exist "config.yaml" (
    echo config.yaml not found, copying config.yaml.dist...
    copy "config.yaml.dist" "config.yaml"

    echo Please, edit your config.yaml file, save it, and close notepad to continue
    :: Open config.yaml in Notepad
    notepad "config.yaml"
) else (
    echo config.yaml found, reusing it.
)


:: Run poetry install
call poetry install

echo this console should be closed automatically in 5 seconds
timeout /t 5