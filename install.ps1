# Instalador de yt-texto para Windows.
# Detecta Python (lo instala con winget si falta), crea un entorno aislado
# en %USERPROFILE%\.yt-texto y deja el comando `yt-texto` en el PATH.
#
# Desde una copia del repo:   powershell -ExecutionPolicy Bypass -File install.ps1
# Sin clonar:                 irm https://raw.githubusercontent.com/Juanpablo9717/youtube-transcript/main/install.ps1 | iex
param([switch]$SinAudio)

$ErrorActionPreference = "Stop"
$Repo   = "https://github.com/Juanpablo9717/youtube-transcript"
$Prefix = Join-Path $env:USERPROFILE ".yt-texto"
$Venv   = Join-Path $Prefix "venv"
$Bin    = Join-Path $Prefix "bin"

function Say($msg) { Write-Host "[yt-texto] $msg" -ForegroundColor Cyan }

function Test-Python($exe, $extra) {
    try {
        $out = & $exe @extra -c "import sys, venv; print(sys.version_info >= (3, 9))" 2>$null
        return ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq "True")
    } catch { return $false }
}

function Find-Python {
    # El "python.exe" de WindowsApps es un acceso directo a la Store: Test-Python lo descarta.
    $candidatos = @(
        @{ exe = "py";      extra = @("-3") },
        @{ exe = "python";  extra = @() },
        @{ exe = "python3"; extra = @() }
    )
    Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        ForEach-Object { $candidatos += @{ exe = $_.FullName; extra = @() } }
    foreach ($c in $candidatos) {
        if ((Get-Command $c.exe -ErrorAction SilentlyContinue) -and (Test-Python $c.exe $c.extra)) {
            return $c
        }
    }
    return $null
}

# 1. Python
$py = Find-Python
if (-not $py) {
    Say "No encontre Python 3.9+. Instalandolo con winget..."
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "No hay winget. Instala Python desde https://www.python.org/downloads/ y vuelve a correr este script."
    }
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
    $py = Find-Python
    if (-not $py) { throw "Python se instalo pero no lo encuentro. Abre una terminal nueva y vuelve a correr el script." }
}
$pyVer = & $py.exe @($py.extra) -c "import sys; print(sys.version.split()[0])"
Say "Python $pyVer -> $($py.exe)"

# 2. Entorno aislado
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    Say "Creando entorno en $Venv"
    & $py.exe @($py.extra) -m venv $Venv
}
$vpy = Join-Path $Venv "Scripts\python.exe"
& $vpy -m pip install --quiet --upgrade pip

# 3. Paquete (desde la copia local si existe, si no desde GitHub)
$extra = if ($SinAudio) { "" } else { "[audio]" }
$local = if ($PSScriptRoot) { Join-Path $PSScriptRoot "pyproject.toml" } else { $null }
if ($local -and (Test-Path $local)) {
    $spec = "$PSScriptRoot$extra"
} else {
    $spec = "yt-texto$extra @ $Repo/archive/refs/heads/main.zip"
}
Say "Instalando dependencias (la primera vez puede tardar unos minutos)..."
& $vpy -m pip install --quiet --upgrade $spec
if ($LASTEXITCODE -ne 0) { throw "Fallo pip install." }

# 4. Comando en el PATH (solo un .cmd, para no tapar otros python.exe)
New-Item -ItemType Directory -Force $Bin | Out-Null
Set-Content -Encoding ascii (Join-Path $Bin "yt-texto.cmd") "@`"$Venv\Scripts\yt-texto.exe`" %*"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($userPath -split ";") -notcontains $Bin) {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$Bin", "User")
    Say "Agregue $Bin a tu PATH (abre una terminal nueva para usarlo)."
}
$env:Path = "$env:Path;$Bin"

Say "Listo. Prueba:  yt-texto `"https://www.youtube.com/watch?v=...`""
