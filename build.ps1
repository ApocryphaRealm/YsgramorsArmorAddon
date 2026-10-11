<#
build.ps1 - build the Ysgramor's Armor addon package.

    build.ps1 [-Version X.Y.Z] [-SourcePlugin <path to the ORIGINAL YsgramorsArmor.esp>] [-OutRoot <folder>]

The version comes from the VERSION file (written by version-gate.ps1 - never by hand). The source
plugin is DeSepticOasis's untouched YsgramorsArmor.esp (Nexus SE 130153, v1.0), found in the MO2
instances unless -SourcePlugin says otherwise; it is read, never written. The package lands in
"7. current test builds\Ysgramor's Armor addon <version>\" with:

    YsgramorsArmor.esp                      their plugin with our records added (tools\Add-YsgramorsArmorRecipes.py)
    Scripts\YsgramorsArmorTombGate.pex      the tomb gate, compiled by the Creation Kit's compiler
    Source\Scripts\YsgramorsArmorTombGate.psc
    README.txt, NOTICE.md, LICENSE-generator-GPL-3.0.txt
#>
param(
    [string]$Version,
    [string]$SourcePlugin,
    [string]$OutRoot = 'D:\Claude output\7. current test builds'
)
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
if (-not $Version) { $Version = (Get-Content -LiteralPath (Join-Path $repo 'VERSION') -Raw).Trim() }
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "VERSION file holds '$Version', not X.Y.Z" }

if (-not $SourcePlugin) {
    $candidates = @(
        "D:\modlists\Njordlinger\mods\Ysgramor's Armor\YsgramorsArmor.esp",
        "C:\Modlists\Apostasy\mods\Ysgramor's Armor\YsgramorsArmor.esp"
    )
    $SourcePlugin = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $SourcePlugin) { throw "the original YsgramorsArmor.esp was not found; pass -SourcePlugin" }
}

$out = Join-Path $OutRoot "Ysgramor's Armor addon $Version"
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Recurse -Force }
New-Item -ItemType Directory -Force -Path $out, (Join-Path $out 'Scripts'), (Join-Path $out 'Source\Scripts') | Out-Null

Write-Host "== plugin"
& python (Join-Path $repo 'tools\Add-YsgramorsArmorRecipes.py') $SourcePlugin (Join-Path $out 'YsgramorsArmor.esp')
if ($LASTEXITCODE -ne 0) { throw "generator failed ($LASTEXITCODE)" }

Write-Host "== script"
$compile = "$(@(& py -3 'D:\Claude output\.MD\resolvers\resolve.py' find compile-papyrus)[0])".Trim()   # by role
& powershell -NoProfile -ExecutionPolicy Bypass -File $compile -Source (Join-Path $repo 'tools\YsgramorsArmorTombGate.psc') -OutDir (Join-Path $out 'Scripts')
if ($LASTEXITCODE -ne 0) { throw "script compile failed ($LASTEXITCODE)" }
Copy-Item -LiteralPath (Join-Path $repo 'tools\YsgramorsArmorTombGate.psc') -Destination (Join-Path $out 'Source\Scripts\')

Write-Host "== documents"
$readme = Get-Content -LiteralPath (Join-Path $repo 'README.md') -Raw
$readme = [regex]::Replace($readme, '(?m)^Version \d+\.\d+\.\d+', "Version $Version")   # stamped from VERSION, never typed
Set-Content -LiteralPath (Join-Path $out 'README.txt') -Value $readme -NoNewline -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $repo 'NOTICE.md') -Destination (Join-Path $out 'NOTICE.md')
Copy-Item -LiteralPath (Join-Path $repo 'LICENSE') -Destination (Join-Path $out 'LICENSE-generator-GPL-3.0.txt')

Get-ChildItem -LiteralPath $out -Recurse -File | ForEach-Object { "  " + $_.FullName.Substring($out.Length + 1) + "  " + $_.Length }
Write-Host "built $out"
