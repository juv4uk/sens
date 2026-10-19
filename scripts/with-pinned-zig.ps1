[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs = @()
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$versionFile = Join-Path $repoRoot ".zig-version"
if (-not (Test-Path -LiteralPath $versionFile -PathType Leaf)) {
    throw "Missing repository-pinned Zig version file: $versionFile"
}

$version = (Get-Content -LiteralPath $versionFile -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Unsupported Zig pin '$version' in .zig-version; expected a stable x.y.z version."
}

if ($env:LOCALAPPDATA) {
    $cacheRoot = Join-Path $env:LOCALAPPDATA "SENS\zig"
} else {
    $cacheRoot = Join-Path $HOME ".cache\SENS\zig"
}
$installDir = Join-Path $cacheRoot "zig-x86_64-windows-$version"
$zigExe = Join-Path $installDir "zig.exe"

$installedVersion = $null
if (Test-Path -LiteralPath $zigExe -PathType Leaf) {
    $installedVersion = (& $zigExe version 2>$null | Out-String).Trim()
}
if ($installedVersion -ne $version) {
    $indexUri = "https://ziglang.org/download/index.json"
    Write-Host "Resolving pinned Zig $version from the official Zig download index..."
    $index = Invoke-RestMethod -Uri $indexUri
    $releaseProperty = $index.PSObject.Properties[$version]
    if ($null -eq $releaseProperty) {
        throw "Pinned Zig $version was not found in the official download index."
    }

    $assetProperty = $releaseProperty.Value.PSObject.Properties["x86_64-windows"]
    if ($null -eq $assetProperty) {
        throw "Official Zig $version release has no x86_64 Windows archive."
    }
    $asset = $assetProperty.Value
    $expectedUri = "https://ziglang.org/download/$version/zig-x86_64-windows-$version.zip"
    if ($asset.tarball -ne $expectedUri) {
        throw "Unexpected official Zig archive URI '$($asset.tarball)'; refusing to download."
    }
    # Pin the exact Windows artifact digest here as well as the Zig version.
    # Update this allowlist only with an intentional repository toolchain change.
    $pinnedHashes = @{
        "0.16.0" = "68659eb5f1e4eb1437a722f1dd889c5a322c9954607f5edcf337bc3684a75a7e"
    }
    if (-not $pinnedHashes.ContainsKey($version)) {
        throw "No repository-pinned Windows x86_64 SHA-256 for Zig $version; update this script with the toolchain pin."
    }
    $expectedHash = $pinnedHashes[$version].ToLowerInvariant()
    $indexHash = ([string]$asset.shasum).ToLowerInvariant()
    if ($indexHash -ne $expectedHash) {
        throw "Official Zig index digest differs from the repository pin for $version."
    }

    $archive = Join-Path $env:TEMP "sens-zig-$version-$PID.zip"
    $extractRoot = Join-Path $env:TEMP "sens-zig-extract-$PID"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $expectedUri -OutFile $archive
        $actualHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Zig archive SHA-256 mismatch: expected $expectedHash, got $actualHash."
        }

        if (Test-Path -LiteralPath $extractRoot) {
            Remove-Item -LiteralPath $extractRoot -Recurse -Force
        }
        New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null
        Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot -Force
        $extractedDir = Join-Path $extractRoot "zig-x86_64-windows-$version"
        $extractedExe = Join-Path $extractedDir "zig.exe"
        if (-not (Test-Path -LiteralPath $extractedExe -PathType Leaf)) {
            throw "Expected zig.exe was not found in the pinned Zig archive."
        }

        New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
        if (Test-Path -LiteralPath $installDir) {
            Remove-Item -LiteralPath $installDir -Recurse -Force
        }
        Move-Item -LiteralPath $extractedDir -Destination $installDir
    } finally {
        if (Test-Path -LiteralPath $archive) {
            Remove-Item -LiteralPath $archive -Force
        }
        if (Test-Path -LiteralPath $extractRoot) {
            Remove-Item -LiteralPath $extractRoot -Recurse -Force
        }
    }
}

$actualVersion = (& $zigExe version | Out-String).Trim()
if ($actualVersion -ne $version) {
    throw "Pinned Zig mismatch: .zig-version requires '$version', installed binary reports '$actualVersion'."
}

# Scope the tool selection to the command started by this script; do not mutate
# the machine-wide or user-wide PATH and do not relax the repository's version pin.
$env:ZIG = $zigExe
$env:PATH = "$installDir;$env:PATH"
Write-Host "ZIG=$env:ZIG ($actualVersion)"
Write-Host "Running: $Command $($CommandArgs -join ' ')"

& $Command @CommandArgs
if ($null -eq $LASTEXITCODE) {
    exit 0
}
exit $LASTEXITCODE
