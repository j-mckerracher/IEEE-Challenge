# Extract all .zip archives in fresco-data-6-9-26 into unzipped-data.

$SourceDir = "C:\Users\jmckerra\Code\IEEE-GSC-Challenge\fresco-data-6-9-26"
$DestDir = Join-Path $SourceDir "unzipped-data"

Add-Type -AssemblyName System.IO.Compression.FileSystem

if (-not (Test-Path $DestDir)) {
    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
}

$zipFiles = Get-ChildItem -Path $SourceDir -Filter "*.zip" -File | Sort-Object Name

if ($zipFiles.Count -eq 0) {
    Write-Warning "No .zip files found in $SourceDir"
    exit 0
}

$total = $zipFiles.Count
$index = 0
$failed = @()

foreach ($zip in $zipFiles) {
    $index++
    Write-Host "[$index/$total] Extracting $($zip.Name) ..."

    try {
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zip.FullName, $DestDir, $true)
    }
    catch {
        $failed += $zip.Name
        Write-Error "Failed to extract $($zip.Name): $_"
    }
}

if ($failed.Count -eq 0) {
    Write-Host "Done. Extracted $total archive(s) to $DestDir"
}
else {
    Write-Warning "Finished with $($failed.Count) failure(s): $($failed -join ', ')"
    exit 1
}
