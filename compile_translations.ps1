# Add gettext tools to PATH
$env:Path += ";C:\Program Files\gettext-iconv\bin"

# Use the current directory instead of hardcoded paths
$currentDir = Get-Location
Write-Host "Current directory: $currentDir"

# Define paths using relative paths
$localeDir = Join-Path -Path $currentDir -ChildPath "locale\ko\LC_MESSAGES"
$poFile = Join-Path -Path $localeDir -ChildPath "django.po"
$moFile = Join-Path -Path $localeDir -ChildPath "django.mo"

Write-Host "PO file path: $poFile"
Write-Host "MO file path: $moFile"

# Check if the PO file exists
if (-not (Test-Path $poFile)) {
    Write-Host "Error: PO file not found at $poFile"
    exit 1
}

# Create a temporary file
$tempFile = Join-Path -Path "C:\Temp" -ChildPath "django_ko.po"
Write-Host "Creating temporary file at: $tempFile"

# Ensure temp directory exists
if (-not (Test-Path "C:\Temp")) {
    New-Item -ItemType Directory -Path "C:\Temp" | Out-Null
}

# Copy the content directly
Get-Content $poFile -Raw | Out-File -FilePath $tempFile -Encoding utf8

# Run msgfmt to compile
Write-Host "Running msgfmt to compile translation..."
& msgfmt -o $moFile $tempFile

# Output results
if ($LASTEXITCODE -eq 0) {
    Write-Host "Translation file compiled successfully!"
} else {
    Write-Host "Failed to compile translation file. Error code: $LASTEXITCODE"
}

# Clean up
if (Test-Path $tempFile) {
    Remove-Item -Path $tempFile -Force
    Write-Host "Temporary file removed."
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Korean translation compiled successfully."
} else {
    Write-Host "Error compiling Korean translation."
}
