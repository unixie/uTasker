Write-Output "Installing Python requirements into .venv"
# Assuming Windows only for Powershell (otherwise use sh)
if (Test-Path -Path .venv) {
    Write-Output ".venv already exists, exiting"
    Exit 0
} else {
    python -m venv --clear --upgrade-deps .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt --require-virtualenv --prefer-binary
Write-Output "..\..\..\lib" | Out-File -FilePath .venv\Lib\site-packages\this.pth
Write-Output "Done!"
