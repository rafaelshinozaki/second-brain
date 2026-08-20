<#
  Backup of the Second Brain on Windows (PowerShell port of backup.sh).
  Neo4j Community has no reliable hot backup, so we stop Neo4j for a few seconds,
  dump offline with an ephemeral container, then start it again.
  Backups go to ./backups with 14-day retention.

  Manual run:   pwsh -File scripts\backup.ps1
  Scheduled:    see scripts\register-backup-task.ps1
#>
$ErrorActionPreference = 'Stop'

$Dir  = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Dest = Join-Path $Dir 'backups'
$Data = Join-Path $Dir 'data\neo4j\data'
$Stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$RetentionDays = 14
$Image = 'neo4j:5.26.0'

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Set-Location $Dir

Write-Host "== Second Brain backup $Stamp =="

# 1) Stop only Neo4j.
docker compose stop neo4j | Out-Null

try {
    # 2) Offline dump. Bypass the image entrypoint and run as root so it can write /backups.
    $tmpDump = Join-Path $Dest 'neo4j.dump'
    Remove-Item -Force $tmpDump -ErrorAction SilentlyContinue

    docker run --rm --user 0:0 --entrypoint neo4j-admin `
        -v "${Data}:/data" `
        -v "${Dest}:/backups" `
        $Image `
        database dump neo4j --to-path=/backups | Out-Null

    if (Test-Path $tmpDump) {
        $final = Join-Path $Dest "neo4j-$Stamp.dump"
        Move-Item -Force $tmpDump $final
        $size = '{0:N1} MB' -f ((Get-Item $final).Length / 1MB)
        Write-Host "OK  Neo4j graph -> neo4j-$Stamp.dump ($size)"
    } else {
        Write-Warning "FAILED to dump Neo4j"
    }
}
finally {
    # 3) Start Neo4j again no matter what.
    docker compose start neo4j | Out-Null
    Write-Host "OK  Neo4j restarted"
}

# 4) Config (compose + config + .env, which holds the Neo4j password).
$cfgZip = Join-Path $Dest "config-$Stamp.zip"
$cfgItems = @('docker-compose.yml', 'config\config.yaml', '.env') |
    ForEach-Object { Join-Path $Dir $_ } | Where-Object { Test-Path $_ }
if ($cfgItems) {
    Compress-Archive -Path $cfgItems -DestinationPath $cfgZip -Force
    Write-Host "OK  config -> config-$Stamp.zip"
}

# 5) Retention.
$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem $Dest -File | Where-Object {
    ($_.Extension -in '.dump', '.zip') -and $_.LastWriteTime -lt $cutoff
} | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "== Done (retention: $RetentionDays days, dir: $Dest) =="
