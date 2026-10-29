# GARAKLAND platform release zip (excludes .git, .vercel, local secrets)
$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root "release"
$zip = Join-Path $outDir "GARAKLAND_PLATFORM_v1.zip"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
if (Test-Path $zip) { Remove-Item $zip -Force }
$staging = Join-Path $env:TEMP ("garakland_zip_" + [guid]::NewGuid().ToString("n"))
Copy-Item -Path $root -Destination $staging -Recurse -Force
foreach ($drop in @(".git", ".vercel", ".env.local", "__pycache__", "release")) {
  $p = Join-Path $staging $drop
  if (Test-Path $p) { Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue }
}
Get-ChildItem -Path $staging -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zip -Force
Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Created $zip"
