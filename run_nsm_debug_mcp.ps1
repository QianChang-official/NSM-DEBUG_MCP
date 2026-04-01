param(
    [string]$Config = "NSM-DEBUG_MCP_R1.example.yaml"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Test-Path ".venv/Scripts/python.exe") {
    .\.venv\Scripts\python.exe src/nsm_debug_mcp/server.py $Config
}
else {
    py -3 src/nsm_debug_mcp/server.py $Config
}