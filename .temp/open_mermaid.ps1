Add-Type -AssemblyName System.Web
$mermaid = Get-Content 'C:\Users\vinic\workspace_antigravity\Avatar\.temp\architecture.mermaid' -Raw
$encoded = [System.Web.HttpUtility]::UrlEncode($mermaid)
Start-Process "https://mermaid.live/edit#pako:$encoded"
