# Juez único (sesión independiente de Claude Opus vía Claude Code) para un debate.
# 1) Anonimiza el debate (A/B al azar).
# 2) Arma una carpeta aislada fuera del repo con el documento, resultados, código y
#    el debate anonimizado (sin debate/ original, para que no vea los nombres).
# 3) Corre el juez allí y guarda el dictamen junto al debate, revelando quién era quién.
# Uso: .\debate\juez.ps1 debate\<hilo>.md [-Previos debate\<anterior>.md, ...]
# Los debates previos se anonimizan con las mismas letras y van como previo_N.md.
param(
    [Parameter(Mandatory = $true)][string]$Hilo,
    [string[]]$Previos = @(),
    [string]$Modelo = 'claude-opus-5-5'
)

$env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8

$repo = Split-Path $PSScriptRoot -Parent
$Hilo = (Resolve-Path $Hilo).Path
$nombre = [IO.Path]::GetFileNameWithoutExtension($Hilo)

$asig = Get-Random -Minimum 0 -Maximum 2
$anonimo = & (Join-Path $PSScriptRoot 'anonimizar.ps1') $Hilo -Asignacion $asig

$aislada = Join-Path $env:LOCALAPPDATA "debate-juez\$nombre"
if (Test-Path $aislada) { Remove-Item -Recurse -Force $aislada }
New-Item -ItemType Directory -Force $aislada | Out-Null
Copy-Item (Join-Path $repo 'Proyecto de investigación IA vs. modelos estadísticos en trading de corto plazo.md') $aislada
Copy-Item (Join-Path $repo 'resultados') $aislada -Recurse
Get-ChildItem $repo -Filter *.py | Copy-Item -Destination $aislada
Copy-Item (Join-Path $PSScriptRoot 'JUEZ.md') $aislada
Copy-Item $anonimo (Join-Path $aislada 'debate.md')
$n = 1
foreach ($p in $Previos) {
    $ap = & (Join-Path $PSScriptRoot 'anonimizar.ps1') (Resolve-Path $p).Path -Asignacion $asig
    Copy-Item $ap (Join-Path $aislada "previo_$n.md"); $n++
}

$prompt = 'Leé JUEZ.md y seguí sus instrucciones al pie de la letra para juzgar debate.md (y, si existen, los debates previos previo_*.md, con las mismas letras A/B). Usá solo lectura de archivos y búsqueda web; no ejecutes comandos ni modifiques nada. Devolvé únicamente el informe en markdown.'

Push-Location $aislada
try { $dictamen = claude -p $prompt --model $Modelo --allowedTools 'Read,Glob,Grep,WebSearch,WebFetch' --disallowedTools 'Bash,PowerShell,Edit,Write,NotebookEdit,Agent' | Out-String }
finally { Pop-Location }

$mapa = Get-Content (Join-Path $env:LOCALAPPDATA "debate-mapas\$nombre.md.txt") -Raw -Encoding utf8
$salida = Join-Path (Split-Path $Hilo) "$nombre.dictamen.md"
$cuerpo = "# Dictamen del juez: $nombre`n`nJuez: $Modelo (sesión independiente de Claude Code, sin acceso a la conversación del debate), sobre la copia anonimizada.`n`n" +
          $dictamen.Trim() + "`n`n---`n**Revelación (después del dictamen):** $($mapa.Trim())`n"
Set-Content -Path $salida -Value $cuerpo -Encoding utf8
$salida
