# Native Word export fallback for Windows runtimes without bundled LibreOffice.
param([string]$ReportPath = "$PSScriptRoot/../report/Google_Local_Analysis_Report.docx")
$resolved = (Resolve-Path -LiteralPath $ReportPath).Path
$pdfPath = [IO.Path]::ChangeExtension($resolved, '.pdf')
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($resolved, $false, $true)
    $document.Repaginate()
    $document.ExportAsFixedFormat($pdfPath, 17)
    Write-Output "Exported $pdfPath"
} finally {
    if ($document) { $document.Close($false); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
    if ($word) { $word.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
}
