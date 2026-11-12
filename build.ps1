<#
build.ps1 - build the Ysgramor's Armor addon package.

    build.ps1 [-Version X.Y.Z] [-SourcePlugin <path to the ORIGINAL YsgramorsArmor.esp>] [-OutRoot <folder>]

The version comes from the VERSION file (written by version-gate.ps1 - never by hand). The source
plugin is DeSepticOasis's untouched YsgramorsArmor.esp (Nexus SE 130153, v1.0), found in the MO2
instances unless -SourcePlugin says otherwise; it is read, never written. The package lands in
"7. current test builds\Ysgramor's Armor addon <version>\" as a FOMOD installer (since 1.1.0):

    fomod\info.xml, fomod\ModuleConfig.xml  the installer; its one page asks when the tomb opens
    Common\ - always installed:
    YsgramorsArmor.esp                     their plugin with our records added (tools\Add-YsgramorsArmorRecipes.py)
    Scripts\YsgramorsArmorTombQuest.pex     the tomb quest script, compiled by the Creation Kit's compiler
    Scripts\YsgramorsArmorTombPlayer.pex    its player alias script - re-arms the quest's poll on every load
    Source\Scripts\YsgramorsArmorTombQuest.psc, Source\Scripts\YsgramorsArmorTombPlayer.psc
    README.txt, NOTICE.md, LICENSE-generator-GPL-3.0.txt
    NoCompanions\YsgramorsArmor - No Companions requirement.esp   the installer option "From the start (no Companions
                                            questline)": opens the tomb without the questline; not installed by default
#>
param(
    [string]$Version,
    [string]$SourcePlugin,
    [string]$OutRoot = 'D:\Claude output\7. current test builds\Skyrim - Ysgramor''s Armor addon'   # where the pipeline reads it (was the parent folder: 1.1.0 landed beside, not in, the package root, 2026-11-11)
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

$pkg = Join-Path $OutRoot "Ysgramor's Armor addon $Version"
$out = Join-Path $pkg 'Common'          # the files the installer always installs
# Never deleted here: an earlier package of this number is moved to .MD\backups first.
if (Test-Path -LiteralPath $pkg) { throw "$pkg already exists - move it to backups first; this build never deletes a package" }
New-Item -ItemType Directory -Force -Path $out, (Join-Path $out 'Scripts'), (Join-Path $out 'Source\Scripts'), (Join-Path $pkg 'NoCompanions'), (Join-Path $pkg 'fomod') | Out-Null

Write-Host "== plugin"
& python (Join-Path $repo 'tools\Add-YsgramorsArmorRecipes.py') $SourcePlugin (Join-Path $out 'YsgramorsArmor.esp') (Join-Path $pkg 'NoCompanions\YsgramorsArmor - No Companions requirement.esp')
if ($LASTEXITCODE -ne 0) { throw "generator failed ($LASTEXITCODE)" }

Write-Host "== scripts"
$compile = "$(@(& py -3 'D:\Claude output\.MD\resolvers\resolve.py' find compile-papyrus)[0])".Trim()   # by role
foreach ($script in 'YsgramorsArmorTombQuest', 'YsgramorsArmorTombPlayer') {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $compile -Source (Join-Path $repo "tools\$script.psc") -OutDir (Join-Path $out 'Scripts')
    if ($LASTEXITCODE -ne 0) { throw "script compile failed: $script ($LASTEXITCODE)" }
    Copy-Item -LiteralPath (Join-Path $repo "tools\$script.psc") -Destination (Join-Path $out 'Source\Scripts\')
}

Write-Host "== documents"
$readme = Get-Content -LiteralPath (Join-Path $repo 'README.md') -Raw
$readme = [regex]::Replace($readme, '(?m)^Version \d+\.\d+\.\d+', "Version $Version")   # stamped from VERSION, never typed
Set-Content -LiteralPath (Join-Path $out 'README.txt') -Value $readme -NoNewline -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $repo 'NOTICE.md') -Destination (Join-Path $out 'NOTICE.md')
Copy-Item -LiteralPath (Join-Path $repo 'LICENSE') -Destination (Join-Path $out 'LICENSE-generator-GPL-3.0.txt')

Write-Host "== installer"
Copy-Item -LiteralPath (Join-Path $repo 'fomod\ModuleConfig.xml') -Destination (Join-Path $pkg 'fomod\')
$info = Get-Content -LiteralPath (Join-Path $repo 'fomod\info.xml') -Raw
$info = [regex]::Replace($info, '<Version>[^<]*</Version>', "<Version>$Version</Version>")   # stamped from VERSION
Set-Content -LiteralPath (Join-Path $pkg 'fomod\info.xml') -Value $info -NoNewline -Encoding UTF8
foreach ($x in 'info.xml', 'ModuleConfig.xml') { [xml](Get-Content -LiteralPath (Join-Path $pkg "fomod\$x") -Raw) | Out-Null }   # throws on malformed XML

Get-ChildItem -LiteralPath $pkg -Recurse -File | ForEach-Object { "  " + $_.FullName.Substring($pkg.Length + 1) + "  " + $_.Length }
Write-Host "built $pkg"
