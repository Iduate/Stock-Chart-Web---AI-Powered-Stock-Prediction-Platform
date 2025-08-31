#!/usr/bin/env powershell
# Manual Django translation compiler for Korean
# This script manually creates a simple PO file and compiles it

# Add gettext tools to PATH
$env:Path += ";C:\Program Files\gettext-iconv\bin"

Write-Host "Starting manual Korean translation compilation..."

# Define paths
$tempDir = "C:\Temp"
$tempPoFile = "$tempDir\django_ko.po"
$moDir = "C:\Users\Hp\Desktop\단가행\Stock Chart Web\locale\ko\LC_MESSAGES"
$moFile = "$moDir\django.mo"

# Ensure directories exist
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}
if (-not (Test-Path $moDir)) {
    New-Item -ItemType Directory -Path $moDir -Force | Out-Null
    Write-Host "Created output directory: $moDir"
}

# Create a minimal valid PO file
$poContent = @"
# Korean translation for Stock Chart Web
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: ko\n"

msgid "Home"
msgstr "홈"

msgid "Chart"
msgstr "차트"
"@

# Write content to temp file
$poContent | Out-File -FilePath $tempPoFile -Encoding utf8

# Display file creation info
if (Test-Path $tempPoFile) {
    Write-Host "Created temp PO file: $tempPoFile"
    Write-Host "Size: $((Get-Item $tempPoFile).Length) bytes"
}

# Run msgfmt to compile
Write-Host "Running msgfmt to compile PO to MO file..."
$command = "msgfmt -o `"$moFile`" `"$tempPoFile`""
Write-Host "Command: $command"

# Execute the command and capture output
$output = & cmd /c "msgfmt -o `"$moFile`" `"$tempPoFile`" 2>&1"
$exitCode = $LASTEXITCODE

# Show output and status
Write-Host "Command output: $output"
Write-Host "Exit code: $exitCode"

# Check result
if ($exitCode -eq 0) {
    Write-Host "Success! MO file created at: $moFile" -ForegroundColor Green
} else {
    Write-Host "Error! Failed to compile translation." -ForegroundColor Red
}

# Clean up
if (Test-Path $tempPoFile) {
    Remove-Item -Path $tempPoFile -Force
    Write-Host "Temp file removed."
}

Write-Host "Process completed."
