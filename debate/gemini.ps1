# Pide a Gemini (Antigravity CLI) su turno en un hilo de debate y lo imprime.
# Uso: .\debate\gemini.ps1 debate\AAAA-MM-DD-tema.md
param(
    [Parameter(Mandatory = $true)][string]$Hilo,
    [string]$Modelo = 'gemini-3.8-flash-high'
)

$env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8

if (-not (Test-Path $Hilo)) { throw "No existe el hilo: $Hilo" }

$prompt = @"
Sos Gemini, participante de un debate de ideas con Claude sobre este repo.
1. Leé debate/PROTOCOLO.md y respetá sus reglas.
2. Leé el hilo '$Hilo' completo.
3. Leé los archivos del repo que necesites para fundamentar (usá tu herramienta de lectura de archivos; NO ejecutes comandos de shell).
4. Escribí SOLO tu próximo turno en markdown, empezando por la crítica al último turno de Claude.
No modifiques ningún archivo: devolvé el texto y Claude lo agregará al hilo.
"@

agy -p $prompt --model $Modelo --mode plan --print-timeout 600s
