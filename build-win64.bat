@echo off

:: Remove old dist files
echo "Cleaning..."
if exist .\dist\Tyler (
  del /s /q .\dist\Tyler
  rmdir /s /q .\dist\Tyler
)
echo "Cleaning done!"

:: Build new dist
echo "Compiling..."
call .\venv\Scripts\activate
pyinstaller .\tyler.spec
call deactivate
echo "Compiling done!"

:: Make zip package
echo "Building package..."
for /f %%i in ('git.exe rev-parse --abbrev-ref HEAD') do set branch=%%i
for /f %%i in ('git.exe rev-parse --short HEAD') do set commit=%%i
"C:\Program Files\7-zip\7z.exe" a -tzip ".\dist\tyler@%branch%-%commit%-win64.zip" ".\dist\Tyler"
echo "Building done!"