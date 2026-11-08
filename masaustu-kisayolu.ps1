# Haber Masası için Başlat menüsü ve masaüstü kısayolu oluşturur.
# Kısayol, uygulamayı Edge'de adres çubuğu olmadan kendi penceresinde açar.
# Kullanım:  powershell -ExecutionPolicy Bypass -File masaustu-kisayolu.ps1 -Url https://KULLANICI.github.io/haber-masasi/
# Ayrıca her sabah belirtilen saatte uygulamayı açan bir Windows zamanlanmış görevi kurar; uygulama açılınca
# bugünün baskısı yoksa kendiliğinden hazırlar. Bilgisayar o saatte kapalıysa açıldığında çalışır.
param(
    [Parameter(Mandatory = $true)][string]$Url,
    [string]$Saat = "08:00"
)

$edge = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Error "Microsoft Edge bulunamadı."; exit 1 }

$appDir = Join-Path $env:LOCALAPPDATA "HaberMasasi"
New-Item -ItemType Directory -Force $appDir | Out-Null
$icon = Join-Path $appDir "app.ico"
Copy-Item (Join-Path $PSScriptRoot "docs\icons\app.ico") $icon -Force

$shell = New-Object -ComObject WScript.Shell
$targets = @(
    (Join-Path ([Environment]::GetFolderPath("Programs")) "Haber Masası.lnk"),
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "Haber Masası.lnk")
)
foreach ($path in $targets) {
    $lnk = $shell.CreateShortcut($path)
    $lnk.TargetPath = $edge
    $lnk.Arguments = "--app=$Url"
    $lnk.IconLocation = $icon
    $lnk.Description = "Almanya ve Türkiye haberleri"
    $lnk.Save()
}
$action = New-ScheduledTaskAction -Execute $edge -Argument "--app=$Url"
$trigger = New-ScheduledTaskTrigger -Daily -At $Saat
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Haber Masası sabah güncellemesi" -Action $action -Trigger $trigger -Settings $settings `
    -Description "Haber Masası uygulamasını açar; uygulama bugünün baskısını hazırlar." -Force | Out-Null
Write-Host "Her gün $Saat'de uygulama açılacak (Görev Zamanlayıcı: 'Haber Masası sabah güncellemesi')."
Write-Host "Kısayollar oluşturuldu. Başlat menüsünde 'Haber Masası'na sağ tıklayıp 'Görev çubuğuna sabitle'yi seçin."
