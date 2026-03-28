"""HTML report generator - self-contained, framework-agnostic."""

from __future__ import annotations

import html
import json
import time

from .models import TestReport, TestStatus, TestCategory


def generate_html_report(report: TestReport, output_path: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(report.start_time))
    fw = report.site_framework

    # Category aggregation
    cat_stats: dict[str, dict] = {}
    for pr in report.pages:
        for t in pr.tests:
            c = t.category.value
            if c not in cat_stats:
                cat_stats[c] = {"passed": 0, "failed": 0, "warning": 0, "skipped": 0}
            cat_stats[c][t.status.value] += 1

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Report - {_e(report.base_url)}</title>
<style>
:root {{
    --bg:#0f1117;--s1:#1a1d27;--s2:#242836;--bdr:#2e3348;
    --txt:#e1e4ed;--dim:#8b8fa3;
    --pass:#22c55e;--passbg:rgba(34,197,94,.1);
    --fail:#ef4444;--failbg:rgba(239,68,68,.1);
    --warn:#f59e0b;--warnbg:rgba(245,158,11,.1);
    --skip:#6b7280;--acc:#6366f1;--accl:#818cf8;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',-apple-system,sans-serif;background:var(--bg);color:var(--txt);line-height:1.6}}
.ctr{{max-width:1200px;margin:0 auto;padding:24px}}
.hdr{{background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#4338ca 100%);padding:40px 0;margin-bottom:32px;border-bottom:3px solid var(--acc)}}
.hdr .ctr{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}}
.hdr h1{{font-size:28px;font-weight:700;color:#fff}}
.hdr h1 span{{color:var(--accl)}}
.hdr .meta{{color:#c4b5fd;font-size:14px;text-align:right}}
.hdr .url{{font-size:16px;color:#e0e7ff;margin-top:4px;word-break:break-all}}
.hdr .fw-badge{{display:inline-block;padding:4px 12px;border-radius:20px;background:rgba(99,102,241,.2);color:var(--accl);font-size:13px;font-weight:600;margin-top:6px}}
.sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:32px}}
.sc{{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;padding:20px;text-align:center}}
.sc .n{{font-size:36px;font-weight:700}}.sc .l{{font-size:13px;color:var(--dim);margin-top:4px}}
.sc.p .n{{color:var(--pass)}}.sc.f .n{{color:var(--fail)}}.sc.w .n{{color:var(--warn)}}.sc.t .n{{color:var(--accl)}}
.pr{{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;padding:24px;text-align:center;margin-bottom:32px}}
.ring{{display:inline-block;position:relative;width:120px;height:120px}}
.ring svg{{transform:rotate(-90deg)}}.ring .rt{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:28px;font-weight:700}}
.cats h2,.detail h2{{font-size:20px;margin-bottom:16px;color:var(--accl)}}
.cg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:32px}}
.cc{{background:var(--s1);border:1px solid var(--bdr);border-radius:8px;padding:16px;display:flex;justify-content:space-between;align-items:center}}
.cc .cn{{font-weight:600;font-size:14px}}.cc .cs{{display:flex;gap:12px;font-size:13px}}
.cc .cs .p{{color:var(--pass)}}.cc .cs .f{{color:var(--fail)}}.cc .cs .w{{color:var(--warn)}}
.ps{{margin-bottom:24px}}
.ph{{background:var(--s1);border:1px solid var(--bdr);border-radius:12px 12px 0 0;padding:16px 20px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;transition:background .2s}}
.ph:hover{{background:var(--s2)}}
.ph .pu{{font-weight:600;font-size:15px;word-break:break-all}}
.ph .pt{{color:var(--dim);font-size:13px;margin-top:2px}}
.ph .bs{{display:flex;gap:8px;flex-shrink:0}}
.bd{{padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600}}
.bd.p{{background:var(--passbg);color:var(--pass)}}.bd.f{{background:var(--failbg);color:var(--fail)}}
.bd.w{{background:var(--warnbg);color:var(--warn)}}.bd.fw{{background:rgba(99,102,241,.15);color:var(--accl)}}
.pb{{background:var(--s2);border:1px solid var(--bdr);border-top:none;border-radius:0 0 12px 12px;display:none}}
.pb.open{{display:block}}
.tt{{width:100%;border-collapse:collapse}}
.tt th{{text-align:left;padding:10px 16px;font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--bdr)}}
.tt td{{padding:10px 16px;border-bottom:1px solid var(--bdr);font-size:13px;vertical-align:top}}
.tt tr:last-child td{{border-bottom:none}}
.dot{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px}}
.dot.passed{{background:var(--pass)}}.dot.failed{{background:var(--fail)}}.dot.warning{{background:var(--warn)}}.dot.skipped{{background:var(--skip)}}
.td{{margin-top:6px;padding:8px 12px;background:var(--bg);border-radius:6px;font-size:12px;color:var(--dim);font-family:Consolas,Monaco,monospace;white-space:pre-wrap;word-break:break-word;max-height:200px;overflow-y:auto}}
.ul{{margin-bottom:32px}}.ul h2{{font-size:20px;margin-bottom:16px;color:var(--accl)}}
.ul ul{{list-style:none}}.ul li{{padding:8px 16px;border-bottom:1px solid var(--bdr);font-size:13px;font-family:monospace}}
.ul li:nth-child(even){{background:var(--s1)}}
.flt{{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap}}
.fb{{padding:6px 16px;border-radius:20px;border:1px solid var(--bdr);background:var(--s1);color:var(--txt);cursor:pointer;font-size:13px;transition:all .2s}}
.fb:hover,.fb.a{{background:var(--acc);border-color:var(--acc);color:#fff}}
.ft{{text-align:center;padding:24px;color:var(--dim);font-size:13px;border-top:1px solid var(--bdr);margin-top:40px}}
@media(max-width:768px){{.hdr .ctr{{flex-direction:column;text-align:center}}.hdr .meta{{text-align:center}}.sg{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>

<div class="hdr"><div class="ctr">
    <div>
        <h1>Web <span>Auto Tester</span> Report</h1>
        <div class="url">{_e(report.base_url)}</div>
        <span class="fw-badge">{_e(fw.name.value)}{' v' + _e(fw.version) if fw.version else ''}</span>
    </div>
    <div class="meta">
        <div>{timestamp}</div>
        <div>Duration: {report.duration_seconds:.1f}s</div>
        <div>{len(report.pages)} page(s) tested</div>
    </div>
</div></div>

<div class="ctr">

<div class="sg">
    <div class="sc t"><div class="n">{report.total_tests}</div><div class="l">Total Tests</div></div>
    <div class="sc p"><div class="n">{report.total_passed}</div><div class="l">Passed</div></div>
    <div class="sc f"><div class="n">{report.total_failed}</div><div class="l">Failed</div></div>
    <div class="sc w"><div class="n">{report.total_warnings}</div><div class="l">Warnings</div></div>
</div>

<div class="pr">{_ring(report.pass_rate)}</div>

<div class="cats"><h2>Results by Category</h2><div class="cg">
{_cat_cards(cat_stats)}
</div></div>

<div class="flt">
    <button class="fb a" onclick="filt('all',this)">All</button>
    <button class="fb" onclick="filt('failed',this)">Failed</button>
    <button class="fb" onclick="filt('warning',this)">Warnings</button>
    <button class="fb" onclick="filt('passed',this)">Passed</button>
</div>

<h2 style="font-size:20px;color:var(--accl);margin-bottom:16px">Detailed Results</h2>
{_page_sections(report)}

<div class="ul">
    <h2>Discovered URLs ({len(report.discovered_urls)})</h2>
    <ul>{"".join(f'<li>{_e(u)}</li>' for u in report.discovered_urls)}</ul>
</div>

</div>

<div class="ft">Generated by Web Auto Tester v1.0.0 &middot; Go Digital Technology Consulting LLP</div>

<script>
function tog(id){{document.getElementById(id).classList.toggle('open')}}
function filt(s,btn){{
    document.querySelectorAll('.fb').forEach(b=>b.classList.remove('a'));
    btn.classList.add('a');
    document.querySelectorAll('.tt tr[data-s]').forEach(r=>{{
        r.style.display=(s==='all'||r.dataset.s===s)?'':'none';
    }});
}}
document.addEventListener('DOMContentLoaded',()=>{{
    document.querySelectorAll('.ps[data-f="true"] .pb').forEach(b=>b.classList.add('open'));
}});
</script>
</body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def _e(t: str) -> str:
    return html.escape(str(t))


def _ring(rate: float) -> str:
    c = 2 * 3.14159 * 50
    off = c - (rate / 100) * c
    clr = "#22c55e" if rate >= 80 else "#f59e0b" if rate >= 60 else "#ef4444"
    return (f'<div class="ring"><svg width="120" height="120" viewBox="0 0 120 120">'
            f'<circle cx="60" cy="60" r="50" stroke="var(--bdr)" stroke-width="10" fill="none"/>'
            f'<circle cx="60" cy="60" r="50" stroke="{clr}" stroke-width="10" fill="none" '
            f'stroke-dasharray="{c}" stroke-dashoffset="{off}" stroke-linecap="round"/>'
            f'</svg><div class="rt" style="color:{clr}">{rate:.0f}%</div></div>'
            f'<div style="margin-top:8px;color:var(--dim);font-size:14px">Pass Rate</div>')


def _cat_cards(stats: dict) -> str:
    return "\n".join(
        f'<div class="cc"><div class="cn">{_e(c)}</div>'
        f'<div class="cs"><span class="p">{s["passed"]}P</span>'
        f'<span class="f">{s["failed"]}F</span>'
        f'<span class="w">{s["warning"]}W</span></div></div>'
        for c, s in sorted(stats.items())
    )


def _page_sections(report: TestReport) -> str:
    parts = []
    for i, pr in enumerate(report.pages):
        pid = f"p{i}"
        has_fail = pr.failed > 0
        fw_name = pr.page.framework.name.value

        badges = []
        if fw_name != "Unknown / Static HTML":
            badges.append(f'<span class="bd fw">{_e(fw_name)}</span>')
        if pr.failed:
            badges.append(f'<span class="bd f">{pr.failed} Fail</span>')
        if pr.warnings:
            badges.append(f'<span class="bd w">{pr.warnings} Warn</span>')
        if pr.passed:
            badges.append(f'<span class="bd p">{pr.passed} Pass</span>')

        rows = []
        for t in pr.tests:
            det = ""
            if t.details:
                det = f'<div class="td">{_e(json.dumps(t.details, indent=2, default=str))}</div>'
            dur = f"{t.duration_ms:.0f}ms" if t.duration_ms > 0 else "-"
            rows.append(
                f'<tr data-s="{t.status.value}">'
                f'<td><span class="dot {t.status.value}"></span>{_e(t.name)}</td>'
                f'<td>{_e(t.category.value)}</td>'
                f'<td>{_e(t.message)}{det}</td><td>{dur}</td></tr>'
            )

        parts.append(
            f'<div class="ps" data-f="{str(has_fail).lower()}">'
            f'<div class="ph" onclick="tog(\'{pid}\')">'
            f'<div><div class="pu">{_e(pr.page.url)}</div>'
            f'<div class="pt">{_e(pr.page.title)} &middot; HTTP {pr.page.status_code}</div></div>'
            f'<div class="bs">{"".join(badges)}</div></div>'
            f'<div id="{pid}" class="pb"><table class="tt">'
            f'<thead><tr><th>Test</th><th>Category</th><th>Result</th><th>Time</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></div>'
        )
    return "\n".join(parts)
