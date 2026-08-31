param(
    [string]$Target = (Join-Path $PSScriptRoot "generated")
)

$ErrorActionPreference = "Stop"

if (Test-Path -LiteralPath $Target) {
    throw "Refusing to overwrite existing Java quickstart target: $Target"
}

New-Item -ItemType Directory -Path $Target | Out-Null
atlas adapter init enterprise-intake --target $Target --language java
atlas adapter init operation-outcome --target $Target --language java

$javac = Get-Command javac -ErrorAction Stop
$java = Get-Command java -ErrorAction Stop
$sourceRoot = Join-Path $Target "atlas-adapters-java\src"
$classes = Join-Path $Target "classes"
$javaFiles = Get-ChildItem -LiteralPath $sourceRoot -Recurse -Filter *.java | ForEach-Object { $_.FullName }
New-Item -ItemType Directory -Path $classes | Out-Null
& $javac.Source -d $classes @javaFiles
if ($LASTEXITCODE -ne 0) {
    throw "Java quickstart compilation failed."
}

& $java.Source -cp $classes com.atlas.adoption.enterpriseintake.EnterpriseIntakeScaffoldSmoke
& $java.Source -cp $classes com.atlas.adoption.operationoutcome.OperationOutcomeScaffoldSmoke
Write-Output "Java Bridge quickstart passed: $($javaFiles.Count) sources compiled; both synthetic smoke programs passed."
