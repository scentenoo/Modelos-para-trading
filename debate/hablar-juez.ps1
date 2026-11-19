# Retoma la sesión del juez que dictaminó un debate, para hablar con él directamente.
# El juez conserva todo lo que leyó y verificó. Sigue sin poder escribir ni ejecutar comandos.
# Uso (en una terminal normal, no dentro de otra sesión de Claude Code):
#   .\debate\hablar-juez.ps1 2026-11-17-evaluacion-ideas
param(
    [Parameter(Mandatory = $true)][string]$Debate,
    [string]$Modelo = 'claude-opus-5-5'
)

$Debate = [IO.Path]::GetFileNameWithoutExtension($Debate)
$aislada = Join-Path $env:LOCALAPPDATA "debate-juez\$Debate"
if (-not (Test-Path $aislada)) { throw "No hay sesión del juez para '$Debate'. Corré antes .\debate\juez.ps1." }

# Claude Code guarda las sesiones por carpeta; se toma la última del juez y se retoma por su id
# (--continue no encuentra las sesiones creadas con claude -p).
$clave = $aislada -replace '[:\\\.]', '-'
$sesiones = Join-Path $env:USERPROFILE ".claude\projects\$clave"
$ultima = Get-ChildItem $sesiones -Filter *.jsonl -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $ultima) { throw "No encontré la sesión del juez en $sesiones" }

Push-Location $aislada
try {
    claude --resume $ultima.BaseName --model $Modelo `
        --allowedTools 'Read,Glob,Grep,WebSearch,WebFetch' `
        --disallowedTools 'Bash,PowerShell,Edit,Write,NotebookEdit,Agent'
}
finally { Pop-Location }
