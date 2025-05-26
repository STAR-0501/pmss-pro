@echo off
REM 递归查找所有 .py 文件并执行 autopep8 -i (排除指定文件夹)
for /f "delims=" %%f in ('dir /s /b /a-d *.py ^| findstr /v \\.venv ^| findstr /v \\.conda') do (
    echo Formatting "%%f"...
    autopep8 -i "%%f"
)
echo Formatting complete.