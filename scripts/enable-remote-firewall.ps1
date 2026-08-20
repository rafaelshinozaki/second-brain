<#
  Opens the Windows Firewall (inbound, Private profile, LocalSubnet only) for the
  Second Brain ports so machines on your LAN can reach it. Run as Administrator.
  Remove later with:  Get-NetFirewallRule -DisplayName 'Second Brain*' | Remove-NetFirewallRule
#>
$ErrorActionPreference = 'Stop'

$rules = @(
    @{ Name = 'Second Brain MCP (8020)';            Port = 8020 },
    @{ Name = 'Second Brain Neo4j Browser (7474)';  Port = 7474 },
    @{ Name = 'Second Brain Neo4j Bolt (7687)';     Port = 7687 }
)

foreach ($r in $rules) {
    Get-NetFirewallRule -DisplayName $r.Name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    # Profile Any so it works whether Windows labels the LAN Public or Private;
    # RemoteAddress LocalSubnet keeps it reachable ONLY from your local network.
    New-NetFirewallRule -DisplayName $r.Name -Direction Inbound -Action Allow `
        -Protocol TCP -LocalPort $r.Port -Profile Any -RemoteAddress LocalSubnet | Out-Null
    Write-Host "OK  regra criada: $($r.Name)"
}
Write-Host "Firewall liberado para a LAN (subnet local, qualquer perfil)."
