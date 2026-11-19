# Crea una copia anonimizada de un debate para el juez: Claude y Gemini pasan a
# "Participante A/B", asignados al azar. El mapa se guarda fuera del repo,
# para que el juez no pueda leerlo.
# Uso: .\debate\anonimizar.ps1 debate\2026-11-17-idea2-pead-llm.md
# -Asignacion 0 o 1 fija las letras (para anonimizar varios debates con las mismas).
param([Parameter(Mandatory = $true)][string]$Hilo, [int]$Asignacion = -1)

$texto = Get-Content $Hilo -Raw -Encoding utf8

# Proteger nombres de productos que no son participantes.
$protegidos = @('Claude Haiku', 'Claude Code', 'claude-haiku', 'Claude Opus', 'Claude Sonnet', 'gemini-3', 'Gemini CLI', 'gemini.ps1')
$i = 0
$guarda = @{}
foreach ($p in $protegidos) {
    $marca = "@@P$i@@"; $guarda[$marca] = $p
    $texto = $texto.Replace($p, $marca); $i++
}

$azar = if ($Asignacion -in 0, 1) { $Asignacion } else { Get-Random -Minimum 0 -Maximum 2 }
if ($azar -eq 0) { $mapa = @{ Claude = 'Participante A'; Gemini = 'Participante B' } }
else             { $mapa = @{ Claude = 'Participante B'; Gemini = 'Participante A' } }

$texto = $texto -replace '\bClaude\b', $mapa.Claude -replace '\bGemini\b', $mapa.Gemini
foreach ($m in $guarda.Keys) { $texto = $texto.Replace($m, $guarda[$m]) }

$dir = Join-Path (Split-Path $Hilo) 'anonimo'
New-Item -ItemType Directory -Force $dir | Out-Null
$salida = Join-Path $dir (Split-Path $Hilo -Leaf)
Set-Content -Path $salida -Value $texto -Encoding utf8

$mapaDir = Join-Path $env:LOCALAPPDATA 'debate-mapas'
New-Item -ItemType Directory -Force $mapaDir | Out-Null
"Claude = $($mapa.Claude); Gemini = $($mapa.Gemini)" |
    Set-Content (Join-Path $mapaDir ((Split-Path $Hilo -Leaf) + '.txt')) -Encoding utf8

$salida
