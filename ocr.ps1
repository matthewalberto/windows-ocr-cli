# OCR images with the OCR engine built into Windows 10 and 11 (Windows.Media.Ocr).
# Nothing to install and nothing leaves the machine. Runs in Windows PowerShell 5.1.
# Keep this file ASCII-only: Windows PowerShell 5.1 misreads UTF-8 without a BOM.
#
# Two modes:
#   Folder mode: OCR every page folder made by render.py.
#     Layout <DataDir>\<doc>\p001.png, p002.png ...
#     Writes <DataDir>\<doc>.ocr.txt with one "===== PAGE nnn =====" block per page.
#       powershell -NoProfile -ExecutionPolicy Bypass -File ocr.ps1 -DataDir <dir>
#
#   Image mode: OCR one or more image files (PNG, JPEG, TIFF, BMP, GIF).
#     Writes <image>.ocr.txt next to each image, or into -OutDir.
#       powershell -NoProfile -ExecutionPolicy Bypass -File ocr.ps1 -Image a.png,b.jpg [-OutDir out]
#
# -Language picks the recognizer (default en-US). The language's OCR pack must be installed
# (Settings > Time & language > Language). Exit 3 means no engine for that language.
param(
    [string]$DataDir,
    [string[]]$Image,
    [string]$OutDir,
    [string]$Language = 'en-US',
    [switch]$ListLanguages
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics, ContentType = WindowsRuntime]
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTaskGeneric.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }

$available = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages | ForEach-Object { $_.LanguageTag }
if ($ListLanguages) { $available; exit 0 }

$lang = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]::new($Language)
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if ($null -eq $engine) {
    Write-Output "NO OCR ENGINE for $Language. Installed: $($available -join ', ')"
    exit 3
}
$maxDim = [Windows.Media.Ocr.OcrEngine]::MaxImageDimension
Write-Output "engine: $($engine.RecognizerLanguage.LanguageTag), max image dimension $maxDim px"

function Read-ImageText([string]$path) {
    $full = (Resolve-Path -LiteralPath $path).Path
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($full)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bmp = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        if ($bmp.PixelWidth -gt $maxDim -or $bmp.PixelHeight -gt $maxDim) {
            Write-Warning "$path is $($bmp.PixelWidth)x$($bmp.PixelHeight); the engine only reads up to $maxDim px. Render at a lower dpi."
        }
        $res = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
        return ($res.Lines | ForEach-Object { $_.Text })
    } finally {
        $stream.Dispose()
    }
}

function Write-Utf8([string]$out, [string]$text) {
    # Write to a temp file, then move it into place, so a crash never leaves half a file.
    $tmp = $out + '.tmp'
    [System.IO.File]::WriteAllText($tmp, $text, (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -Force $tmp $out
}

if ($Image) {
    if ($OutDir) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
    foreach ($img in $Image) {
        $lines = @(Read-ImageText $img)
        $dir = if ($OutDir) { $OutDir } else { Split-Path -Parent (Resolve-Path -LiteralPath $img).Path }
        $out = Join-Path $dir ((Split-Path -Leaf $img) + '.ocr.txt')
        Write-Utf8 $out (($lines -join "`r`n") + "`r`n")
        Write-Output "$img : $($lines.Count) lines -> $out"
    }
    exit 0
}

if (-not $DataDir) {
    Write-Output 'Give -DataDir <folder of page folders> or -Image <file>[,<file>...]. -ListLanguages shows installed languages.'
    exit 2
}

foreach ($d in Get-ChildItem -Path $DataDir -Directory) {
    $sb = New-Object System.Text.StringBuilder
    $pages = @(Get-ChildItem -Path $d.FullName -Filter 'p*.png' | Sort-Object Name)
    if ($pages.Count -eq 0) { continue }
    foreach ($png in $pages) {
        [void]$sb.AppendLine("===== PAGE $($png.BaseName.Substring(1)) =====")
        foreach ($line in (Read-ImageText $png.FullName)) { [void]$sb.AppendLine($line) }
    }
    $out = Join-Path $DataDir ($d.Name + '.ocr.txt')
    Write-Utf8 $out $sb.ToString()
    Write-Output "$($d.Name): $($pages.Count) pages, $($sb.Length) chars -> $out"
}
