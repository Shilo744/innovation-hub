# Innovation Hub - GitHub Auto Update Script
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Innovation Hub - עדכון GitHub"

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   עדכון אתר Innovation Hub ל-GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# בדיקה שזה ריפו Git
git rev-parse --is-inside-work-tree 2>$null | Out-Null
if (-not $?) {
    Write-Host "[שגיאה] התיקייה הזו אינה ריפו Git." -ForegroundColor Red
    Read-Host "לחץ Enter ליציאה"
    exit 1
}

# בדיקת שינויים
Write-Host "[1/4] בודק שינויים..." -ForegroundColor Yellow
$changes = git status --porcelain
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host ""
    Write-Host "אין שינויים מקומיים." -ForegroundColor Green
    # בכל זאת ננסה לדחוף commits שלא הועלו עדיין
    $ahead = git rev-list --count "@{u}..HEAD" 2>$null
    if ($ahead -and [int]$ahead -gt 0) {
        Write-Host "יש $ahead commits שעוד לא הועלו - דוחף ל-GitHub..." -ForegroundColor Yellow
        git push origin main
        if ($?) {
            Write-Host "✓ הועלה בהצלחה!" -ForegroundColor Green
            $repoUrl = (git remote get-url origin).Trim() -replace '\.git$', ''
            Start-Process $repoUrl
        }
    } else {
        Write-Host "הכל מסונכרן עם GitHub." -ForegroundColor Green
    }
    exit 0
}

git status --short
Write-Host ""

# הוספת קבצים
Write-Host "[2/4] מוסיף את כל הקבצים (כולל חדשים)..." -ForegroundColor Yellow
git add -A
if (-not $?) {
    Write-Host "שגיאה ב-git add" -ForegroundColor Red
    Read-Host "לחץ Enter ליציאה"
    exit 1
}

# Commit
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
Write-Host "[3/4] שומר commit..." -ForegroundColor Yellow
git commit -m "Auto-update: $stamp"
if (-not $?) {
    Write-Host "שגיאה ב-git commit" -ForegroundColor Red
    Read-Host "לחץ Enter ליציאה"
    exit 1
}

# Push
Write-Host "[4/4] מעלה ל-GitHub..." -ForegroundColor Yellow
git push origin main
if (-not $?) {
    Write-Host ""
    Write-Host "שגיאה ב-git push - בדוק חיבור לאינטרנט והרשאות GitHub" -ForegroundColor Red
    Read-Host "לחץ Enter ליציאה"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ✓ העדכון הושלם בהצלחה!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# פתיחת GitHub בדפדפן
Write-Host "פותח את GitHub בדפדפן..." -ForegroundColor Cyan
$repoUrl = (git remote get-url origin).Trim()
$repoUrl = $repoUrl -replace '\.git$', ''
Start-Process $repoUrl

