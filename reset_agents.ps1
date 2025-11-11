# Reset all agent state files
Write-Host "🧹 Cleaning up agent state files..." -ForegroundColor Cyan

$stateDir = "src\data\simulated_trades"
$stateFiles = Get-ChildItem -Path $stateDir -Filter "agent_*_state.json" -ErrorAction SilentlyContinue

if ($stateFiles.Count -eq 0) {
    Write-Host "✅ No state files found - already clean!" -ForegroundColor Green
} else {
    Write-Host "Found $($stateFiles.Count) state file(s) to delete:" -ForegroundColor Yellow
    foreach ($file in $stateFiles) {
        Write-Host "  - $($file.Name)" -ForegroundColor Yellow
    }
    
    $confirm = Read-Host "`nDelete these files? (y/n)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        foreach ($file in $stateFiles) {
            Remove-Item $file.FullName -Force
            Write-Host "  ✅ Deleted $($file.Name)" -ForegroundColor Green
        }
        Write-Host "`n✅ All agent state files deleted!" -ForegroundColor Green
        Write-Host "   New agents will start fresh with $100k balance" -ForegroundColor Cyan
    } else {
        Write-Host "`n❌ Cancelled - no files deleted" -ForegroundColor Red
    }
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
