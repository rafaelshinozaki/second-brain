<#
  Registers a Windows Scheduled Task that runs the Second Brain backup daily.
  Runs only when the current user is logged on (Docker Desktop needs the user session).
  Re-run this script to update the task. Remove with:
      Unregister-ScheduledTask -TaskName 'SecondBrainBackup' -Confirm:$false
#>
$ErrorActionPreference = 'Stop'

$TaskName = 'SecondBrainBackup'
$Script   = (Resolve-Path (Join-Path $PSScriptRoot 'backup.ps1')).Path
$WorkDir  = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`"" `
    -WorkingDirectory $WorkDir

# Daily at 03:15. Change -At to whatever time your PC is usually on and logged in.
$trigger = New-ScheduledTaskTrigger -Daily -At 3:15AM

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# Run as the current user, only when logged on (interactive token so Docker is reachable).
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "Registered scheduled task '$TaskName' (daily 03:15)."
Write-Host "Run it now with:  Start-ScheduledTask -TaskName '$TaskName'"
