#Requires -Version 7
<#
.SYNOPSIS
Turn a Daily note into the pieces of a manual Patreon post (Windows).

.DESCRIPTION
Windows / PowerShell Core port of scripts/patreon_post.py. The Patreon API v2
is read-only, so posts are created in the browser. This script prepares
everything the browser step needs:

  * title        - the part of the note name in brackets, e.g. "Big Picture Hope"
  * date         - the note's own date (used as the publish date)
  * tags         - the note's frontmatter tags (the same ones the site uses)
  * site_url     - the published vault page for the note
  * body (html)  - intro, then per reading: a linked heading, the quoted
                   verses and the commentary, with Obsidian syntax removed

Writes DIR/post.json, DIR/post-body.html (the raw fragment, identical HTML to
the macOS script) and DIR/post.html - an interactive review page. Open the
page, type your comment anywhere in the article, then click "Copy post body"
and paste into the Patreon editor as rich text. Buttons also copy the title,
tags, site URL and publish date for the other composer fields.

Usage:
  patreon_post.ps1 "Daily/2026-10-19 (Big Picture Hope).md" [-Out DIR]
                   [-Copy] [-Open]

  -Copy also puts the raw HTML on the Windows clipboard (rich text) at once.
  -Open opens the review page in your default browser after writing it.

Prints JSON with title, date, tags and site_url.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Note,

    [string]$Out,

    [switch]$Copy,

    [switch]$Open
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SITE = 'https://ashworx-global.github.io/vault'
$SKIP_FROM = '## Harvested verse pages'

# ── helpers ──────────────────────────────────────────────────────────────────

function ConvertTo-Slug([string]$Name) {
    # Mirror scripts/build-site.py so the link matches the published page.
    $s = $Name.Trim().ToLower()
    $s = $s.Replace([char]0x2013, '-').Replace([char]0x2014, '-')   # en/em dash
    $s = [regex]::Replace($s, '[^a-z0-9]+', '-')
    $s = [regex]::Replace($s, '-+', '-')
    return $s.Trim('-')
}

function Split-Frontmatter([string]$Text) {
    # Return (tags, body) from a note whose frontmatter starts on line 1.
    $m = [regex]::Match($Text, '(?s)^---\r?\n(.*?)\r?\n---\r?\n')
    if (-not $m.Success) { return @(), $Text }
    $tags = @([regex]::Matches($m.Groups[1].Value, '(?m)^\s*-\s*(\S+)\s*$') |
        ForEach-Object { $_.Groups[1].Value })
    return $tags, $Text.Substring($m.Index + $m.Length)
}

function ConvertTo-Inline([string]$Line) {
    # Obsidian/markdown inline syntax -> HTML.
    $line = [regex]::Replace($Line, '%%.*?%%', '')
    $line = [regex]::Replace($line, '\[\[(\d+)\]\]\(', '[$1](')     # Logos footnote [[1]](url)
    $line = [regex]::Replace($line, '\[\[[^\]|]*\|([^\]]*)\]\]', '$1')
    $line = [regex]::Replace($line, '\[\[([^\]]*)\]\]', '$1')

    $enc = { param($s) [System.Net.WebUtility]::HtmlEncode($s) }
    $out = [System.Collections.Generic.List[string]]::new()
    $pos = 0
    foreach ($m in [regex]::Matches($line, '\[([^\]]+)\]\(([^)\s]+)\)')) {
        $plainPart = & $enc $line.Substring($pos, $m.Index - $pos)
        $out.Add($plainPart)
        $text, $url = $m.Groups[1].Value, $m.Groups[2].Value
        $a = '<a href="{0}">{1}</a>' -f (& $enc $url), (& $enc $text)
        $out.Add($(if ($text -match '^\d+$') { "<sup>$a</sup>" } else { $a }))
        $pos = $m.Index + $m.Length
    }
    $out.Add((& $enc $line.Substring($pos)))
    $text = [string]::Concat($out)
    $text = [regex]::Replace($text, '\*\*(.+?)\*\*', '<strong>$1</strong>')
    return [regex]::Replace($text, '(?<![\w*])_(.+?)_(?![\w*])', '<em>$1</em>')
}

function Join-Blocks([string[]]$Lines) {
    # Group consecutive non-blank lines into <p> blocks (line breaks kept).
    # A markdown heading line (#### Daily Prayer) ends the current block and
    # becomes its own <h4>, so it never shows up as literal #### text.
    $blocks = [System.Collections.Generic.List[string]]::new()
    $cur = [System.Collections.Generic.List[string]]::new()
    foreach ($line in (@($Lines) + @(''))) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^#{1,6}\s+(.+)$') {
            if ($cur.Count) {
                $blocks.Add('<p>' + (($cur | ForEach-Object { ConvertTo-Inline $_ }) -join '<br>') + '</p>')
                $cur.Clear()
            }
            $blocks.Add('<h4>' + (ConvertTo-Inline $Matches[1]) + '</h4>')
        }
        elseif ($trimmed) {
            $cur.Add($trimmed)
        }
        elseif ($cur.Count) {
            $blocks.Add('<p>' + (($cur | ForEach-Object { ConvertTo-Inline $_ }) -join '<br>') + '</p>')
            $cur.Clear()
        }
    }
    return $blocks
}

function ConvertTo-PostBody([string]$Body) {
    # Intro + one section per [!bible] callout, minus the verse dump.
    $body = ($Body -split [regex]::Escape($SKIP_FROM), 2)[0]
    $parts = [System.Collections.Generic.List[object]]::new()
    $parts.Add([System.Collections.Generic.List[string]]::new())     # parts[0] is the intro, then one list per reading
    $headings = [System.Collections.Generic.List[object]]::new()
    $headings.Add($null)
    [bool]$inCallout = $false

    foreach ($line in ($body -split '\r?\n')) {
        $m = [regex]::Match($line, '^>\s*\[!bible\][+-]?\s*\[([^\]]+)\]\(([^)\s]+)\)')
        if ($m.Success) {
            [void]$headings.Add(@($m.Groups[1].Value, $m.Groups[2].Value))
            [void]$parts.Add([System.Collections.Generic.List[string]]@())
            $inCallout = $true
            continue
        }
        if ($inCallout) {
            if ($line -match '%%>') { $inCallout = $false }
            continue
        }
        $trim = $line.Trim()
        $partsLast = $parts[$parts.Count - 1]
        $headLast = $headings[$headings.Count - 1]
        if ($trim -match '^(\[\[[^\]]+\]\]\s*)+$') { continue }                    # backlink line
        if ((-not $headLast) -and
            ($trim -match '^(\[[^\]]+\]\([^)]+\)\s*\*?\s*)+$')) {
            continue                                                              # plain reading-links line
        }
        [void]$partsLast.Add($line)
    }

    $out = @(Join-Blocks $parts[0].ToArray())
    for ($i = 1; $i -lt $headings.Count; $i++) {
        $label = $headings[$i][0] -replace '\s+-\s+[\w-]+$', ''                   # drop " - WEB-OFFLINE"
        $out += '<h3><a href="{0}">{1}</a></h3>' -f
            ([System.Net.WebUtility]::HtmlEncode($headings[$i][1])),
            ([System.Net.WebUtility]::HtmlEncode($label))
        $out += @(Join-Blocks $parts[$i].ToArray())
    }
    return $out -join "`n"
}

function ConvertTo-CfHtmlBytes([string]$Fragment) {
    # Wrap an HTML fragment in the CF_HTML ("HTML Format") clipboard envelope.
    $ver = "Version:0.9`r`nStartHTML:{0:D10}`r`nEndHTML:{1:D10}`r`nStartFragment:{2:D10}`r`nEndFragment:{3:D10}`r`n"
    $prefix, $suffix = '<html><body><!--StartFragment-->', '<!--EndFragment--></body></html>'
    $enc = [Text.Encoding]::UTF8
    $hLen = $enc.GetByteCount(($ver -f 0, 0, 0, 0))
    $pLen = $enc.GetByteCount($prefix)
    $fLen = $enc.GetByteCount($Fragment)
    $total = $hLen + $pLen + $fLen + $enc.GetByteCount($suffix)
    $html = ($ver -f 0, $total, ($hLen + $pLen), ($hLen + $pLen + $fLen)) + $prefix + $Fragment + $suffix
    return $enc.GetBytes($html)
}

function Copy-HtmlToClipboard([string]$Fragment) {
    # Put HTML on the Windows clipboard as rich text (CF_HTML). pwsh runs STA
    # by default, which the clipboard API requires.
    if (-not ('Win32.Clip' -as [type])) {
        Add-Type -Namespace Win32 -Name Clip -MemberDefinition @'
[DllImport("user32.dll")] public static extern uint RegisterClipboardFormatW(string fmt);
[DllImport("user32.dll")] public static extern bool OpenClipboard(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool EmptyClipboard();
[DllImport("user32.dll")] public static extern IntPtr SetClipboardData(uint format, IntPtr hMem);
[DllImport("user32.dll")] public static extern bool CloseClipboard();
[DllImport("kernel32.dll")] public static extern IntPtr GlobalAlloc(uint flags, UIntPtr bytes);
[DllImport("kernel32.dll")] public static extern IntPtr GlobalLock(IntPtr hMem);
[DllImport("kernel32.dll")] public static extern bool GlobalUnlock(IntPtr hMem);
'@
    }
    $bytes = ConvertTo-CfHtmlBytes $Fragment
    $fmt = [Win32.Clip]::RegisterClipboardFormatW('HTML Format')
    if (-not [Win32.Clip]::OpenClipboard([IntPtr]::Zero)) { throw 'OpenClipboard failed' }
    try {
        [void][Win32.Clip]::EmptyClipboard()
        $mem = [Win32.Clip]::GlobalAlloc(0x0002, [UIntPtr][uint32]($bytes.Length + 1))
        $ptr = [Win32.Clip]::GlobalLock($mem)
        try { [Runtime.InteropServices.Marshal]::Copy($bytes, 0, $ptr, $bytes.Length) }
        finally { [void][Win32.Clip]::GlobalUnlock($mem) }
        if ([Win32.Clip]::SetClipboardData($fmt, $mem) -eq [IntPtr]::Zero) { throw 'SetClipboardData failed' }
    }
    finally { [void][Win32.Clip]::CloseClipboard() }
}

# ── main ─────────────────────────────────────────────────────────────────────

$notePath = if (Test-Path -LiteralPath $Note) { (Resolve-Path -LiteralPath $Note).Path }
            else { throw "Note not found: $Note" }
$stem = (Get-Item -LiteralPath $notePath).BaseName

$m = [regex]::Match($stem, '^(\d{4}-\d{2}-\d{2})\s*\((.*?)\)?$')
if (-not $m.Success) { throw "Can't read date/title from note name: $stem" }
$date, $title = $m.Groups[1].Value, $m.Groups[2].Value.Trim()

$text = [IO.File]::ReadAllText($notePath)
$tags, $body = Split-Frontmatter $text
$siteUrl = "$SITE/daily/$(ConvertTo-Slug $stem)/"
$postHtml = ConvertTo-PostBody $body
$postHtml += "`n<p>Read it on the site: <a href=`"$siteUrl`">$siteUrl</a></p>"

if (-not $Out) { $Out = Join-Path ([IO.Path]::GetTempPath()) "patreon-$date" }
if (-not [IO.Path]::IsPathRooted($Out)) { $Out = Join-Path (Get-Location) $Out }
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$utf8noBom = [Text.UTF8Encoding]::new($false)

# post-body.html: raw fragment (same HTML the macOS script puts on its clipboard)
[IO.File]::WriteAllText((Join-Path $Out 'post-body.html'), $postHtml, $utf8noBom)
[IO.File]::WriteAllText((Join-Path $Out 'post.json'), (ConvertTo-Json (@{
        title = $title; date = $date; tags = @($tags); site_url = $siteUrl }) -Depth 3),
    $utf8noBom)

# post.html: interactive review page - type your comment, then copy as rich text
$json = ConvertTo-Json -Compress @{ title = $title; date = $date; tags = @($tags); site_url = $siteUrl }
$tagsHtml = [System.Net.WebUtility]::HtmlEncode(($tags -join ', '))
$titleHtml = [System.Net.WebUtility]::HtmlEncode($title)
$carbon = $json   # valid JS object literal (no angle brackets in these fields)

$page = @"
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Patreon draft - $titleHtml</title>
<style>
  body     { font: 15px/1.6 Georgia, 'Times New Roman', serif; margin: 0; }
  .bar     { position: sticky; top: 0; background: #1a1a1a; color: #eee;
             padding: 12px 20px; font-family: Segoe UI, sans-serif; font-size: 13px; }
  .bar b   { color: #ffd98a; }
  .bar .meta span { margin-right: 1.5em; }
  .bar .meta { display: block; }
  button   { font: inherit; background: #ffd98a; border: 0; border-radius: 4px;
             padding: 5px 14px; margin: 6px 8px 0 0; cursor: pointer; }
  button:hover { background: #ffe4ad; }
  #status  { color: #9fe0a0; margin-left: .6em; }
  .hint    { font-family: Segoe UI, sans-serif; font-size: 13px; background: #eef4ff;
             border: 1px solid #c6d4f5; border-radius: 6px; padding: 8px 20px; }
  #body    { max-width: 760px; margin: 16px auto 60px; padding: 24px 32px;
             outline: 2px dashed transparent; }
  #body:hover { outline-color: #f5c862; }
  #body:focus { outline-color: #e6a817; }
  #body a  { color: #1c5ba8; text-decoration: none; border-bottom: 1px dotted #1c5ba8; }
  #body h3 { font-family: 'Segoe UI', sans-serif; margin-top: 1.2em; }
</style>
</head>
<body>
<div class="bar">
  <span class="meta"><span><b>Title</b> $titleHtml</span>
  <span><b>Date</b> $date</span>
  <span><b>Site</b> $siteUrl</span></span>
  <span class="meta"><span><b>Tags</b> $tagsHtml</span></span>
  <button data-copy="body">Copy post body</button>
  <button data-copy="title">Copy title</button>
  <button data-copy="tags">Copy tags</button>
  <button data-copy="url">Copy site URL</button>
  <button data-copy="date">Copy date</button>
  <span id="status"></span>
</div>
<p class="hint">
  &#10004; Edit the dashed article below: click where you want a remark and type it
  (retros, notes, extra links). Then <b>Copy post body</b> &rarr; in the Patreon
  composer click into the body editor and paste (Ctrl+V). Title, tags and publish
  date each have their own composer field - use the other buttons.
</p>
<article id="body" contenteditable="true" spellcheck="true">
$postHtml
</article>
<script>
const DATA = $carbon;
const art = document.getElementById('body');
const status = document.getElementById('status');
function ok (what) {
  status.textContent = '\u2713 ' + what + ' copied';
  setTimeout(() => status.textContent = '', 2500);
}
async function copyPlain (text, what) {
  try { await navigator.clipboard.writeText(text); }
  catch {
    const box = document.createElement('textarea');
    box.value = text; document.body.appendChild(box);
    box.select(); document.execCommand('copy'); box.remove();
  }
  ok(what);
}
async function copyRich () {
  art.focus();
  const sel = getSelection();
  sel.removeAllRanges();
  sel.selectAllChildren(art);
  try {
    await navigator.clipboard.write([new ClipboardItem({
      'text/plain': new Blob([art.innerText], { type: 'text/plain' }),
      'text/html':  new Blob([art.innerHTML], { type: 'text/html' })
    })]);
  }
  catch { document.execCommand('copy'); }
  sel.removeAllRanges();
  art.blur();
  ok('post body');
}
for (const b of document.querySelectorAll('.bar button')) {
  b.addEventListener('click', () => {
    if (b.dataset.copy === 'body') { copyRich().catch(e => status.textContent = String(e)); }
    else { copyPlain(DATA[b.dataset.copy], b.dataset.copy).catch(e => status.textContent = String(e)); }
  });
}
</script>
</body>
</html>
"@
[IO.File]::WriteAllText((Join-Path $Out 'post.html'), $page, $utf8noBom)

if ($Copy) { Copy-HtmlToClipboard $postHtml }
if ($Open) { Start-Process (Join-Path $Out 'post.html') }

ConvertTo-Json -Compress @{
    title = $title; date = $date; tags = @($tags); site_url = $siteUrl }
