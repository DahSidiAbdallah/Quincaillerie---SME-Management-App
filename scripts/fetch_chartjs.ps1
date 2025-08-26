# Download official Chart.js UMD bundle into app/static/js/chart.umd.min.js
# Usage: .\scripts\fetch_chartjs.ps1
$dest = "app/static/js/chart.umd.min.js"
$uri = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js'
Write-Host "Downloading Chart.js from $uri to $dest"
Invoke-WebRequest -Uri $uri -OutFile $dest -UseBasicParsing
Write-Host "Downloaded Chart.js to $dest"
