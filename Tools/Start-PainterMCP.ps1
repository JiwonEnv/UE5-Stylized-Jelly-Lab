$painterExe = 'C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe'
if (Get-Process -Name 'Adobe Substance 3D Painter' -ErrorAction SilentlyContinue) {
    Write-Host 'Painter is already running. If MCP cannot connect, close Painter and run this launcher again.'
    exit 0
}
Start-Process -FilePath $painterExe -ArgumentList '--enable-remote-scripting' -WindowStyle Hidden
