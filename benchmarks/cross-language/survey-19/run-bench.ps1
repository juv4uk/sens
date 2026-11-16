#Requires -Version 5.1
<#
    Cross-language survey — fib / sieve / collatz
    =============================================

    Один і той самий алгоритм на багатьох мовах. Кожне навантаження
    запускається ОКРЕМИМ процесом, міряється повний wall-clock час,
    береться мінімум із кількох прогонів після прогріву.

    Це локальний survey, а НЕ сертифікований Contract 11.9 доказ і НЕ
    глобальний рейтинг мов. Деталі й застереження — у README.md та
    RESULTS.md.

    Приклади:
        powershell -ExecutionPolicy Bypass -File .\run-bench.ps1
        powershell -ExecutionPolicy Bypass -File .\run-bench.ps1 -SkipBuild
        powershell -ExecutionPolicy Bypass -File .\run-bench.ps1 -Smoke
        powershell -ExecutionPolicy Bypass -File .\run-bench.ps1 -SkipBuild -Only Swift,Rust,Zig
#>
param(
    [int]$Fib = 34,
    [int]$Sieve = 5000000,
    [int]$Collatz = 500000,
    [int]$Runs = 3,
    [int]$Warmups = 1,
    [switch]$SkipBuild,
    [switch]$Smoke,
    [string[]]$Only = @()
)

$ErrorActionPreference = 'Continue'
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }
Set-Location -LiteralPath $root

function Say($m) { Write-Host $m }
function F1($v) { $v.ToString('F1', [System.Globalization.CultureInfo]::InvariantCulture) }

# ---------------------------------------------------------------------------
# Fresh environment (Machine + User) — те саме, що бачить новий термінал
# ---------------------------------------------------------------------------
$machine = [Environment]::GetEnvironmentVariables('Machine')
$user    = [Environment]::GetEnvironmentVariables('User')
if ($machine['Path']) {
    $env:Path = if ($user['Path']) { $machine['Path'] + ';' + $user['Path'] } else { $machine['Path'] }
}
if ($user.ContainsKey('SDKROOT')) { $env:SDKROOT = $user['SDKROOT'] }
$env:GOTOOLCHAIN = 'local'

# ---------------------------------------------------------------------------
# Best-effort tool detection
# ---------------------------------------------------------------------------
function Resolve-Tool {
    param([string]$Name, [string[]]$Fallbacks = @())
    $c = Get-Command $Name -ErrorAction SilentlyContinue
    if ($c -and $c.Source) { return $c.Source }
    foreach ($f in $Fallbacks) {
        $g = Get-Item -Path $f -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($g) { return $g.FullName }
    }
    return $null
}

function Find-VcVars {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path -LiteralPath $vswhere) {
        $p = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
        if ($p) {
            $bat = Join-Path $p.Trim() 'VC\Auxiliary\Build\vcvars64.bat'
            if (Test-Path -LiteralPath $bat) { return $bat }
        }
    }
    foreach ($cand in @(
        'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
    )) { if (Test-Path -LiteralPath $cand) { return $cand } }
    return $null
}

$vcvars  = Find-VcVars
$swiftc  = Resolve-Tool 'swiftc'  @("$env:LOCALAPPDATA\Programs\Swift\Toolchains\*\usr\bin\swiftc.exe")
$rustc   = Resolve-Tool 'rustc'   @("$env:USERPROFILE\.cargo\bin\rustc.exe")
$zig     = Resolve-Tool 'zig'     @("$env:LOCALAPPDATA\Microsoft\WinGet\Links\zig.exe")
$go      = Resolve-Tool 'go'      @('C:\Program Files\Go\bin\go.exe')
$javac   = Resolve-Tool 'javac'   @("$env:ProgramFiles\Eclipse Adoptium\jdk-*\bin\javac.exe", 'C:\Program Files\Eclipse Adoptium\jdk-*\bin\javac.exe')
$java    = Resolve-Tool 'java'    @("$env:ProgramFiles\Eclipse Adoptium\jdk-*\bin\java.exe")
$dotnet  = Resolve-Tool 'dotnet'  @('C:\Program Files\dotnet\dotnet.exe')
$fpc     = Resolve-Tool 'fpc'     @('C:\FPC\*\bin\i386-win32\fpc.exe', 'C:\FPC\*\bin\*\fpc.exe')
$deno    = Resolve-Tool 'deno'    @("$env:LOCALAPPDATA\Microsoft\WinGet\Links\deno.exe")
$node    = Resolve-Tool 'node'    @('C:\Program Files\nodejs\node.exe')
$bun     = Resolve-Tool 'bun'     @("$env:USERPROFILE\.bun\bin\bun.exe")
$julia   = Resolve-Tool 'julia'   @("$env:LOCALAPPDATA\Programs\Julia-*\bin\julia.exe")
$lua     = Resolve-Tool 'lua'     @("$env:LOCALAPPDATA\Programs\Lua\bin\lua.exe")
$luajit  = Resolve-Tool 'luajit'  @("$env:LOCALAPPDATA\Programs\LuaJIT\bin\luajit.exe")
$php     = Resolve-Tool 'php'     @("$env:LOCALAPPDATA\Microsoft\WinGet\Packages\PHP.PHP.8.4_*\php.exe")
$ruby    = Resolve-Tool 'ruby'    @('C:\Ruby*\bin\ruby.exe')
$python  = Resolve-Tool 'python'  @("$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe")
$py314   = Resolve-Tool 'python3.14' @("$env:LOCALAPPDATA\Programs\Python\Python314\python.exe")

if ($Smoke) { $Fib = 20; $Sieve = 100000; $Collatz = 20000; $Runs = 2 }

function Test-Runnable($exe) {
    if (-not $exe) { return $false }
    if ($exe -match '^[A-Za-z]:\\' -or $exe.StartsWith('\\')) { return (Test-Path -LiteralPath $exe) }
    return [bool](Get-Command $exe -ErrorAction SilentlyContinue)
}

# ---------------------------------------------------------------------------
# Build stage
# ---------------------------------------------------------------------------
function TryBuild($label, $cmd) {
    Say ("  building {0} ..." -f $label)
    $out = cmd /c $cmd 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Say ("    !! FAILED: {0}" -f $label)
        Say ($out.Trim())
        return $false
    }
    return $true
}

if (-not $SkipBuild) {
    Say "=== BUILD ==="
    $builds = @(
        @{ Name = 'C (MSVC)';    Tool = $vcvars;  Cmd = "call `"$vcvars`" >nul && cl /nologo /O2 /Ob3 /Fe:bench_c.exe /Fo:bench_c.obj bench.c" }
        @{ Name = 'C++ (MSVC)';  Tool = $vcvars;  Cmd = "call `"$vcvars`" >nul && cl /nologo /O2 /Ob3 /EHsc /Fe:bench_cpp.exe /Fo:bench_cpp.obj bench.cpp" }
        @{ Name = 'Rust';        Tool = $rustc;   Cmd = "`"$rustc`" -O -C opt-level=3 -C target-cpu=native bench.rs -o bench_rust.exe" }
        @{ Name = 'Swift';       Tool = $swiftc;  Cmd = "`"$swiftc`" -O -parse-as-library -whole-module-optimization bench.swift -o bench_swift.exe" }
        @{ Name = 'Zig';         Tool = $zig;     Cmd = "`"$zig`" build-exe bench.zig -O ReleaseFast --name bench_zig" }
        @{ Name = 'Go';          Tool = $go;      Cmd = "`"$go`" build -o bench_go.exe bench.go" }
        @{ Name = 'Java';        Tool = $javac;   Cmd = "`"$javac`" -d . Bench.java" }
        @{ Name = 'C# (.NET)';   Tool = $dotnet;  Cmd = "`"$dotnet`" build cs\Bench.csproj -c Release -v quiet --nologo" }
        @{ Name = 'Free Pascal'; Tool = $fpc;     Cmd = "`"$fpc`" -Px86_64 -O3 -obench_pascal.exe bench.pas" }
        @{ Name = 'Deno compile';Tool = $deno;    Cmd = "`"$deno`" compile --no-check -o bench_deno.exe bench.ts" }
    )
    foreach ($b in $builds) {
        if (-not $b.Tool) { Say ("  skip {0} (tool not found)" -f $b.Name); continue }
        TryBuild $b.Name $b.Cmd | Out-Null
    }
    Say ""
}

# ---------------------------------------------------------------------------
# Program registry
# ---------------------------------------------------------------------------
$dotnetExe = Join-Path $root 'cs\bin\Release\net9.0\benchcs.exe'

$programs = @(
    [pscustomobject]@{ Name = 'C (MSVC)';      Exe = "$root\bench_c.exe";       Pre = @() }
    [pscustomobject]@{ Name = 'C++ (MSVC)';    Exe = "$root\bench_cpp.exe";     Pre = @() }
    [pscustomobject]@{ Name = 'Rust';          Exe = "$root\bench_rust.exe";    Pre = @() }
    [pscustomobject]@{ Name = 'Swift';         Exe = "$root\bench_swift.exe";   Pre = @() }
    [pscustomobject]@{ Name = 'Zig';           Exe = "$root\bench_zig.exe";     Pre = @() }
    [pscustomobject]@{ Name = 'Go';            Exe = "$root\bench_go.exe";      Pre = @() }
    [pscustomobject]@{ Name = 'Free Pascal';   Exe = "$root\bench_pascal.exe";  Pre = @() }
    [pscustomobject]@{ Name = 'C# (.NET 9)';   Exe = $dotnetExe;                Pre = @() }
    [pscustomobject]@{ Name = 'Java 21';       Exe = $java;                     Pre = @('-XX:+UseSerialGC', 'Bench') }
    [pscustomobject]@{ Name = 'Deno (native)'; Exe = "$root\bench_deno.exe";    Pre = @() }
    [pscustomobject]@{ Name = 'Node.js';       Exe = $node;                     Pre = @('bench.js') }
    [pscustomobject]@{ Name = 'Bun';           Exe = $bun;                      Pre = @('bench.js') }
    [pscustomobject]@{ Name = 'Julia';         Exe = $julia;                    Pre = @('--startup-file=no', '-O3', 'bench.jl') }
    [pscustomobject]@{ Name = 'LuaJIT';        Exe = $luajit;                   Pre = @('bench.lua') }
    [pscustomobject]@{ Name = 'Python 3.10';   Exe = $python;                   Pre = @('bench.py') }
    [pscustomobject]@{ Name = 'Python 3.14';   Exe = $py314;                    Pre = @('bench.py') }
    [pscustomobject]@{ Name = 'PHP 8.4';       Exe = $php;                      Pre = @('bench.php') }
    [pscustomobject]@{ Name = 'Ruby 3.3';      Exe = $ruby;                     Pre = @('bench.rb') }
    [pscustomobject]@{ Name = 'Lua 5.4';       Exe = $lua;                      Pre = @('bench.lua') }
)

if ($Only.Count -gt 0) {
    $programs = $programs | Where-Object { $n = $_.Name; ($Only | Where-Object { $n -like "*$_*" }).Count -gt 0 }
}

# ---------------------------------------------------------------------------
# Workloads: кожен вимір окремо, щоб бачити, де саме мова провалюється
# ---------------------------------------------------------------------------
$workloads = @(
    [pscustomobject]@{ Key = 'fib';     Args = @("$Fib", '0', '0') }
    [pscustomobject]@{ Key = 'sieve';   Args = @('0', "$Sieve", '0') }
    [pscustomobject]@{ Key = 'collatz'; Args = @('0', '0', "$Collatz") }
)

Say ("=== RUN  fib={0}  sieve={1}  collatz={2}  (warmup={3}, runs={4}) ===" -f $Fib, $Sieve, $Collatz, $Warmups, $Runs)
Say ""

$rows = @()
$reference = @{}

foreach ($p in $programs) {
    if (-not (Test-Runnable $p.Exe)) {
        Say ("  {0,-14} SKIP (missing {1})" -f $p.Name, $p.Exe)
        continue
    }

    $row = [ordered]@{ Name = $p.Name }
    $ok = $true

    foreach ($w in $workloads) {
        # прогрів (перший запуск платить Defender-скан / JIT / page cache)
        for ($i = 0; $i -lt $Warmups; $i++) {
            & $p.Exe @($p.Pre) @($w.Args) > $null 2>&1
        }

        $times = @()
        $output = ''
        for ($i = 0; $i -lt $Runs; $i++) {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $output = (& $p.Exe @($p.Pre) @($w.Args) 2>&1 | Out-String)
            $sw.Stop()
            $times += $sw.Elapsed.TotalMilliseconds
        }

        $best = ($times | Measure-Object -Minimum).Minimum
        $row[$w.Key] = [math]::Round($best, 1)
        $row["$($w.Key)_raw"] = (($times | ForEach-Object { [math]::Round($_, 1) }) -join '/')

        $text = ($output.Trim() -replace "`r", "")
        if (-not $reference.ContainsKey($w.Key)) { $reference[$w.Key] = $text }
        if ($text -ne $reference[$w.Key]) { $ok = $false }
    }

    $row['Total'] = [math]::Round(($row['fib'] + $row['sieve'] + $row['collatz']), 1)
    $row['Match'] = $ok
    $rows += [pscustomobject]$row

    Say ("  {0,-14} fib {1,9}  sieve {2,9}  collatz {3,9}  total {4,9} ms  {5}" -f `
        $p.Name, (F1 $row['fib']), (F1 $row['sieve']), (F1 $row['collatz']), (F1 $row['Total']), $(if ($ok) { 'ok' } else { 'MISMATCH' }))
}

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
Say ""
Say "=== RESULT (best of $Runs, ms) ==="
$sorted = $rows | Sort-Object Total
$hdr = "{0,-2} {1,-16} {2,10} {3,10} {4,10} {5,10} {6,8}"
Say ($hdr -f '#', 'Language', 'fib', 'sieve', 'collatz', 'total', 'vs best')
Say ('-' * 72)
$rank = 1
$fastest = if ($sorted.Count -gt 0) { ($sorted | Select-Object -First 1).Total } else { 0 }
foreach ($r in $sorted) {
    $ratio = if ($fastest -gt 0) { $r.Total / $fastest } else { 1 }
    Say ($hdr -f $rank, $r.Name, (F1 $r.fib), (F1 $r.sieve), (F1 $r.collatz), (F1 $r.Total), ("{0:F2}x" -f $ratio))
    $rank++
}

Say ""
Say "=== Reference output ==="
foreach ($k in @('fib', 'sieve', 'collatz')) {
    Say ("[{0}]" -f $k)
    Say $reference[$k]
}

# ---------------------------------------------------------------------------
# Persist raw results
# ---------------------------------------------------------------------------
function Get-HostSlug {
    $name = (Get-ItemProperty 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -ErrorAction SilentlyContinue).ProcessorNameString
    if (-not $name) { $name = $env:PROCESSOR_IDENTIFIER }
    if (-not $name) { return 'unknown-cpu' }
    $s = $name -replace '\(R\)|\(TM\)|\(tm\)|CPU|@.*$', ''
    $s = ($s -replace '[^A-Za-z0-9]+', '-').Trim('-').ToLowerInvariant()
    $s = $s -replace '^intel-core-', ''
    if (-not $s) { $s = 'unknown-cpu' }
    return $s
}

$stamp    = Get-Date -Format 'yyyyMMdd'
$hostSlug = Get-HostSlug
$outDir   = Join-Path $root ("results\{0}-survey-19-{1}" -f $stamp, $hostSlug)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$csvPath = Join-Path $outDir 'survey-19.csv'
$rows | Select-Object Name, fib, sieve, collatz, Total, Match, fib_raw, sieve_raw, collatz_raw |
    Export-Csv -Path $csvPath -NoTypeInformation -Encoding utf8

$cpuName = (Get-ItemProperty 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -ErrorAction SilentlyContinue).ProcessorNameString
$osInfo  = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue)
$envInfo = [ordered]@{
    stamp    = $stamp
    hostSlug = $hostSlug
    cpu      = $cpuName
    os       = if ($osInfo) { "$($osInfo.Caption) build $($osInfo.BuildNumber)" } else { [Environment]::OSVersion.VersionString }
    ps       = $PSVersionTable.PSVersion.ToString()
    workloads = [ordered]@{ fib = $Fib; sieve = $Sieve; collatz = $Collatz }
    warmups  = $Warmups
    runs     = $Runs
    reference = $reference
}
$jsonPath = Join-Path $outDir 'environment.json'
[System.IO.File]::WriteAllText($jsonPath, ($envInfo | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))

Say ""
Say ("Saved: {0}" -f $csvPath)
Say ("Saved: {0}" -f $jsonPath)
