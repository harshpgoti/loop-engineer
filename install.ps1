# Loop Engineering OS - GitHub installer
# Usage:
#   irm https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.ps1 | iex
#   & ([scriptblock]::Create((irm .../install.ps1))) -UseCwd   # local memory in cwd

param(
    [switch]$DryRun,
    [switch]$NoPath,
    [string]$Workspace,
    [string]$Name = "global",
    [string]$MemoryMode,
    [switch]$UseCwd,
    [string]$Ref = $(if ($env:LOOP_ENGINE_REF) { $env:LOOP_ENGINE_REF } else { "main" })
)

$ErrorActionPreference = "Stop"

$Repo = if ($env:LOOP_ENGINE_REPO) { $env:LOOP_ENGINE_REPO } else { "https://github.com/harshpgoti/loop-engineer.git" }
$LoopHome = if ($env:LOOP_ENGINEER_HOME) { (Resolve-Path $env:LOOP_ENGINEER_HOME).Path } elseif ($env:LOOP_HOME) { (Resolve-Path $env:LOOP_HOME).Path } else { Join-Path $env:USERPROFILE ".loop-engineer" }
$App = Join-Path $LoopHome "app"
$Bin = Join-Path $LoopHome "bin"

if ($UseCwd) {
    $Workspace = (Get-Location).Path
    $MemoryMode = "local"
    if ($Name -eq "global") {
        $Name = Split-Path -Leaf $Workspace
    }
}

if ($MemoryMode -and $MemoryMode -notin @("local", "global")) {
    throw "Invalid -MemoryMode '$MemoryMode'. Valid values: local, global."
}

if (-not $MemoryMode) {
    if ($Workspace) { $MemoryMode = "local" } else { $MemoryMode = "global" }
}

if ($MemoryMode -eq "global") {
    $Workspace = Join-Path $LoopHome "data"
} elseif (-not $Workspace) {
    $Workspace = (Get-Location).Path
}

function Write-Step([string]$Message) { Write-Host "==> $Message" }
function Invoke-Step([scriptblock]$Action, [string]$Label) {
    if ($DryRun) { Write-Host "[dry-run] $Label"; return }
    & $Action
}
function Find-Python {
    foreach ($c in @("python", "python3", "py")) {
        if (Get-Command $c -ErrorAction SilentlyContinue) { return (Get-Command $c).Source }
    }
    throw "Python 3.10+ required."
}
function Test-Git {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git required." }
}
function Add-UserPath([string]$Directory) {
    if ($NoPath) { return }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -split ';' | Where-Object { $_ -eq $Directory }) { return }
    if ($DryRun) { Write-Host "[dry-run] add PATH: $Directory"; return }
    [Environment]::SetEnvironmentVariable("Path", $(if ($userPath) { "$userPath;$Directory" } else { $Directory }), "User")
    $env:Path = "$Directory;$env:Path"
}

Write-Step "Loop Engineer installer"
Write-Step "Home=$LoopHome"
Write-Step "App=$App"
Write-Step "Memory mode=$MemoryMode"
Write-Step "Data workspace=$Workspace"

Test-Git
$Python = Find-Python

Invoke-Step { New-Item -ItemType Directory -Force -Path $LoopHome, $App, (Join-Path $LoopHome "data\registry"), $Bin | Out-Null } "Create directories"

if (Test-Path (Join-Path $App ".git")) {
    Write-Step "Updating app..."
    Invoke-Step { git -C $App fetch origin $Ref --tags; git -C $App checkout $Ref; git -C $App pull --ff-only origin $Ref } "git pull"
} else {
    Write-Step "Cloning app..."
    Invoke-Step { git clone --depth 1 --branch $Ref $Repo $App } "git clone"
}

$LoopCmd = Join-Path $Bin "loop.cmd"
if ($DryRun) {
    Write-Host "[dry-run] write $LoopCmd"
} else {
    @"
@echo off
set "LOOP_ENGINEER_HOME=$LoopHome"
"$Python" "$App\scripts\loop_cli.py" %*
"@ | Set-Content -Path $LoopCmd -Encoding ASCII
}

Add-UserPath $Bin
$env:LOOP_ENGINEER_HOME = $LoopHome

$SetupArgs = @("--workspace", $Workspace, "--name", $Name)
if ($MemoryMode -eq "local") { $SetupArgs += @("--memory-mode", "local") }

Write-Step "Running setup..."
Invoke-Step { & $Python (Join-Path $App "scripts\setup_loop_engine.py") @SetupArgs } "setup"
Invoke-Step { & $Python (Join-Path $App "scripts\doctor.py") --workspace $Workspace } "doctor"

Write-Host ""
Write-Host "Installed."
Write-Host "  Home:        $LoopHome"
Write-Host "  App:         $App"
Write-Host "  Memory mode: $MemoryMode"
Write-Host "  Data:        $Workspace"
Write-Host "  CLI:         loop  (new terminal, or $LoopCmd)"
Write-Host ""
Write-Host "Native slash commands registered for Claude Code, Cursor, Codex, and OpenCode."
Write-Host "Restart your agent (new session) so it picks up the new /commands."
Write-Host "Re-run any time with: loop commands install"
Write-Host ""
Write-Host "Open your agent in: $App"
Write-Host "Then run: /plan-loop"
