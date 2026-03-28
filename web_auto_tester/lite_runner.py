"""
Lite test runner — no browser, no Playwright.

Uses httpx + BeautifulSoup for all checks.
Peak memory: ~50-80 MB (vs 350+ MB with Chromium).
Used automatically when low_memory=True (Render free tier).

Tests covered:
  - Page Load & HTTP status
  - Security Headers
  - SEO Basics
  - Accessibility (HTML-level)
  - Broken Links (HEAD requests)
  - Broken Images (HEAD requests)
  - Framework Detection (HTML/JS signature scanning)
  - Performance (TTFB, response time)
"""

from __future__ import annotations

import asyncio
import gc
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .models import (
    TestReport, PageResult, TestResult, TestStatus, TestCategory,
    DiscoveredPage, FrameworkInfo, DetectedFramework,
)
from .report import generate_html_report


# ── HTTP client settings ──────────────────────────────────────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ── Framework detection from HTML ─────────────────────────────────────────────
def _detect_framework_html(html: str, soup: BeautifulSoup, headers: dict) -> FrameworkInfo:
    name = DetectedFramework.UNKNOWN
    version = None
    is_spa = False
    is_ssr = False
    features: list[str] = []

    # Angular
    if soup.find(attrs={"ng-version": True}):
        name = DetectedFramework.ANGULAR
        version = soup.find(attrs={"ng-version": True}).get("ng-version")
        is_spa = True
    elif re.search(r'window\.getAllAngularTestabilities|ng\.getComponent', html):
        name = DetectedFramework.ANGULAR
        is_spa = True

    # Next.js
    if "__NEXT_DATA__" in html or soup.find(id="__next"):
        name = DetectedFramework.NEXTJS
        is_spa = True
        is_ssr = True

    # React
    if name == DetectedFramework.UNKNOWN:
        if soup.find(id="root") and re.search(r'__reactFiber|__reactInternalInstance', html):
            name = DetectedFramework.REACT
            is_spa = True
        elif "data-reactroot" in html:
            name = DetectedFramework.REACT
            is_spa = True

    # Gatsby
    if soup.find(id="__gatsby"):
        name = DetectedFramework.GATSBY
        is_spa = True
        is_ssr = True

    # Vue / Nuxt
    if name == DetectedFramework.UNKNOWN:
        if soup.find(attrs={"data-v-app": True}) or soup.find(id="__nuxt"):
            name = DetectedFramework.NUXT if "__NUXT__" in html else DetectedFramework.VUE
            is_spa = True
            is_ssr = "__NUXT__" in html
        elif soup.find(id="app") and re.search(r'window\.Vue|__vue_app__', html):
            name = DetectedFramework.VUE
            is_spa = True

    # Svelte
    if name == DetectedFramework.UNKNOWN:
        if soup.find(class_=re.compile(r'svelte-')):
            name = DetectedFramework.SVELTE
            is_spa = True

    # jQuery
    if re.search(r'jquery\.min\.js|jquery-\d|/jquery/', html, re.IGNORECASE):
        if name == DetectedFramework.UNKNOWN:
            name = DetectedFramework.JQUERY
        else:
            features.append("jQuery")

    # UI libraries from HTML signatures
    if soup.find(class_=re.compile(r'^(mat-|MuiButton|ant-btn|chakra-|p-button)')):
        lib = (
            "Angular Material" if soup.find(class_=re.compile(r'^mat-'))
            else "MUI" if soup.find(class_=re.compile(r'^Mui'))
            else "Ant Design" if soup.find(class_=re.compile(r'^ant-'))
            else "Chakra UI" if soup.find(class_=re.compile(r'^chakra-'))
            else "PrimeNG/PrimeReact"
        )
        features.append(lib)

    if soup.find(class_=re.compile(r'\bbtn-primary\b|\bcontainer-fluid\b')):
        features.append("Bootstrap")

    # Server: X-Powered-By header hints
    powered = headers.get("x-powered-by", "")
    if "Next.js" in powered:
        name = DetectedFramework.NEXTJS
        is_ssr = True
    elif "Express" in powered:
        features.append("Express")

    return FrameworkInfo(
        name=name,
        version=version,
        is_spa=is_spa,
        is_ssr=is_ssr,
        features=features,
    )


# ── Crawl (BFS via HTML link extraction) ─────────────────────────────────────
async def _crawl(
    client: httpx.AsyncClient,
    base_url: str,
    max_pages: int,
    max_depth: int,
) -> list[DiscoveredPage]:
    base_domain = urlparse(base_url).netloc
    visited: set[str] = set()
    pages: list[DiscoveredPage] = []

    _EXCLUDE = re.compile(
        r"/api/|\.(pdf|zip|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|css|js|map)(\?|$)"
        r"|mailto:|tel:|javascript:|#$|oauth|callback|logout|signout",
        re.IGNORECASE,
    )

    queue: list[tuple[str, int, str]] = [(base_url.rstrip("/"), 0, "entry")]

    while queue and len(pages) < max_pages:
        url, depth, found_on = queue.pop(0)

        # Normalize
        parsed = urlparse(url)
        norm = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/') or '/'}"
        if norm in visited or _EXCLUDE.search(url):
            continue
        visited.add(norm)

        try:
            t0 = time.perf_counter()
            resp = await client.get(url, follow_redirects=True, timeout=20)
            ttfb_ms = (time.perf_counter() - t0) * 1000

            ct = resp.headers.get("content-type", "")
            if "text/html" not in ct and depth > 0:
                continue

            html = resp.text
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                soup = BeautifulSoup(html, "html.parser")

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            fw = _detect_framework_html(html, soup, dict(resp.headers))

            pages.append(DiscoveredPage(
                url=norm,
                title=title,
                status_code=resp.status_code,
                framework=fw,
                depth=depth,
                found_on=found_on,
                _html=html,
                _soup=soup,
                _resp_headers=dict(resp.headers),
                _ttfb_ms=ttfb_ms,
            ))

            # Enqueue links
            if depth < max_depth:
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    if not href or _EXCLUDE.search(href):
                        continue
                    full = href if href.startswith("http") else urljoin(url + "/", href)
                    if urlparse(full).netloc == base_domain:
                        queue.append((full, depth + 1, norm))

        except Exception:
            pages.append(DiscoveredPage(
                url=norm,
                title="(Failed to load)",
                status_code=0,
                depth=depth,
                found_on=found_on,
            ))

    return pages


# ── Analyzers ─────────────────────────────────────────────────────────────────
async def _check_page_load(dp: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    status = dp.status_code
    ttfb = getattr(dp, "_ttfb_ms", 0)

    if 200 <= status < 300:
        results.append(TestResult(
            name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
            status=TestStatus.PASSED, message=f"Page returned {status}",
            details={"status_code": status}, duration_ms=ttfb,
        ))
    elif 300 <= status < 400:
        results.append(TestResult(
            name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
            status=TestStatus.WARNING, message=f"Redirect {status}",
            details={"status_code": status},
        ))
    elif status == 0:
        results.append(TestResult(
            name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
            status=TestStatus.FAILED, message="Connection failed",
        ))
        return results
    else:
        results.append(TestResult(
            name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
            status=TestStatus.FAILED, message=f"Error {status}",
            details={"status_code": status},
        ))

    soup: BeautifulSoup | None = getattr(dp, "_soup", None)
    if soup:
        text = soup.get_text(separator=" ", strip=True)
        body_len = len(text)
        results.append(TestResult(
            name="Page Has Content", category=TestCategory.PAGE_LOAD,
            status=TestStatus.PASSED if body_len > 10 else TestStatus.WARNING,
            message=f"{body_len} chars of text content" if body_len > 10 else "Very little content",
            details={"text_length": body_len},
        ))

        title = dp.title
        results.append(TestResult(
            name="Page Has Title", category=TestCategory.PAGE_LOAD,
            status=TestStatus.PASSED if title else TestStatus.WARNING,
            message=f"Title: '{title}'" if title else "No page title",
        ))

        # Basic error page detection from text
        text_lower = text.lower()
        errors = []
        if "404" in text_lower and ("not found" in text_lower or "page not found" in text_lower):
            errors.append("404 Not Found")
        if "500" in text_lower and "server error" in text_lower:
            errors.append("500 Server Error")
        if "application error" in text_lower:
            errors.append("Application Error")
        results.append(TestResult(
            name="No Error Page Displayed", category=TestCategory.PAGE_LOAD,
            status=TestStatus.FAILED if errors else TestStatus.PASSED,
            message=f"Errors: {', '.join(errors)}" if errors else "No error indicators",
            details={"errors": errors} if errors else {},
        ))

    results.append(TestResult(
        name="Page Load Time", category=TestCategory.PERFORMANCE,
        status=TestStatus.PASSED if ttfb < 3000 else TestStatus.WARNING if ttfb < 6000 else TestStatus.FAILED,
        message=f"Response time: {ttfb:.0f}ms",
        details={"ttfb_ms": round(ttfb)}, duration_ms=ttfb,
    ))

    return results


async def _check_security_headers(dp: DiscoveredPage) -> list[TestResult]:
    headers = getattr(dp, "_resp_headers", {})
    results: list[TestResult] = []

    checks = [
        ("X-Content-Type-Options", "nosniff", True),
        ("X-Frame-Options", None, True),
        ("Strict-Transport-Security", None, True),
        ("Content-Security-Policy", None, False),
        ("Referrer-Policy", None, False),
        ("Permissions-Policy", None, False),
    ]
    for name, expected, critical in checks:
        val = headers.get(name.lower()) or headers.get(name)
        if val:
            ok = not expected or expected.lower() in val.lower()
            results.append(TestResult(
                name=f"Header: {name}", category=TestCategory.SECURITY_HEADERS,
                status=TestStatus.PASSED if ok else TestStatus.WARNING,
                message=f"{val[:80]}",
            ))
        else:
            results.append(TestResult(
                name=f"Header: {name}", category=TestCategory.SECURITY_HEADERS,
                status=TestStatus.WARNING if critical else TestStatus.SKIPPED,
                message=f"Missing {name}",
            ))

    results.append(TestResult(
        name="HTTPS", category=TestCategory.SECURITY_HEADERS,
        status=TestStatus.PASSED if dp.url.startswith("https://") else TestStatus.FAILED,
        message="HTTPS" if dp.url.startswith("https://") else "Not HTTPS",
    ))
    return results


async def _check_seo(dp: DiscoveredPage) -> list[TestResult]:
    soup: BeautifulSoup | None = getattr(dp, "_soup", None)
    if not soup:
        return []
    results: list[TestResult] = []

    def meta(name: str) -> str | None:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        return tag.get("content") if tag else None

    desc = meta("description")
    if desc and 50 <= len(desc) <= 160:
        results.append(TestResult(name="Meta Description", category=TestCategory.SEO,
            status=TestStatus.PASSED, message=f"{len(desc)} chars"))
    elif desc:
        results.append(TestResult(name="Meta Description", category=TestCategory.SEO,
            status=TestStatus.WARNING, message=f"Length {len(desc)} — ideal 50–160"))
    else:
        results.append(TestResult(name="Meta Description", category=TestCategory.SEO,
            status=TestStatus.WARNING, message="Missing meta description"))

    title = dp.title
    if title and 10 <= len(title) <= 70:
        results.append(TestResult(name="Title Quality", category=TestCategory.SEO,
            status=TestStatus.PASSED, message=f"'{title}' ({len(title)} chars)"))
    elif title:
        results.append(TestResult(name="Title Quality", category=TestCategory.SEO,
            status=TestStatus.WARNING, message=f"Length {len(title)} — ideal 10–70 chars"))

    og_title = meta("og:title")
    og_desc = meta("og:description")
    results.append(TestResult(
        name="Open Graph Tags", category=TestCategory.SEO,
        status=TestStatus.PASSED if og_title and og_desc else TestStatus.WARNING,
        message="OG tags present" if og_title else "Missing OG tags",
    ))

    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        results.append(TestResult(name="Canonical URL", category=TestCategory.SEO,
            status=TestStatus.PASSED, message=canonical["href"][:80]))

    robots = meta("robots")
    if robots and "noindex" in robots.lower():
        results.append(TestResult(name="Robots", category=TestCategory.SEO,
            status=TestStatus.WARNING, message=f"robots: {robots} (noindex blocks crawlers)"))

    return results


async def _check_accessibility(dp: DiscoveredPage) -> list[TestResult]:
    soup: BeautifulSoup | None = getattr(dp, "_soup", None)
    if not soup:
        return []
    results: list[TestResult] = []

    html_tag = soup.find("html")
    lang = html_tag.get("lang", "") if html_tag else ""
    results.append(TestResult(
        name="HTML lang Attribute", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if lang else TestStatus.FAILED,
        message=f"lang='{lang}'" if lang else "Missing lang attribute",
    ))

    h1s = soup.find_all("h1")
    results.append(TestResult(
        name="Single H1 Tag", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if len(h1s) == 1 else TestStatus.WARNING,
        message=f"{len(h1s)} H1 heading(s)" if len(h1s) != 1 else "Exactly one H1",
    ))

    headings = [int(h.name[1]) for h in soup.find_all(re.compile(r'^h[1-6]$'))]
    hier_ok = all(headings[i] - headings[i-1] <= 1 for i in range(1, len(headings)))
    results.append(TestResult(
        name="Heading Hierarchy", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if hier_ok else TestStatus.WARNING,
        message="Correct hierarchy" if hier_ok else "Heading levels skip",
    ))

    imgs_without_alt = soup.find_all("img", alt=False)
    if imgs_without_alt:
        results.append(TestResult(
            name="Images Have Alt Text", category=TestCategory.ACCESSIBILITY,
            status=TestStatus.WARNING,
            message=f"{len(imgs_without_alt)} image(s) missing alt",
        ))
    elif soup.find_all("img"):
        results.append(TestResult(
            name="Images Have Alt Text", category=TestCategory.ACCESSIBILITY,
            status=TestStatus.PASSED, message="All images have alt attributes",
        ))

    landmarks = soup.find_all(["main", "nav", "header", "footer"]) + \
                soup.find_all(attrs={"role": re.compile(r'^(main|navigation|banner|contentinfo)$')})
    results.append(TestResult(
        name="ARIA Landmarks", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if landmarks else TestStatus.WARNING,
        message=f"{len(landmarks)} landmark(s)" if landmarks else "No ARIA landmarks found",
    ))

    viewport = soup.find("meta", attrs={"name": "viewport"})
    results.append(TestResult(
        name="Viewport Meta", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if viewport else TestStatus.WARNING,
        message="Present" if viewport else "Missing viewport meta tag",
    ))

    return results


async def _check_broken_links(
    client: httpx.AsyncClient,
    dp: DiscoveredPage,
    base_domain: str,
) -> list[TestResult]:
    soup: BeautifulSoup | None = getattr(dp, "_soup", None)
    if not soup:
        return []

    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        full = href if href.startswith("http") else urljoin(dp.url + "/", href)
        if urlparse(full).netloc == base_domain:
            links.append({"href": full, "text": (tag.get_text(strip=True) or "")[:50]})

    broken: list[dict] = []
    for link in links[:15]:
        try:
            resp = await client.head(link["href"], follow_redirects=True, timeout=8)
            if resp.status_code >= 400:
                broken.append({"url": link["href"], "text": link["text"], "status": resp.status_code})
        except Exception:
            broken.append({"url": link["href"], "text": link["text"], "status": 0})

    return [TestResult(
        name="No Broken Internal Links", category=TestCategory.BROKEN_LINKS,
        status=TestStatus.FAILED if broken else TestStatus.PASSED,
        message=f"{len(broken)} broken link(s)" if broken else f"All {min(len(links), 15)} internal links OK",
        details={"broken": broken} if broken else {"total_links": len(links), "checked": min(len(links), 15)},
    )]


async def _check_broken_images(
    client: httpx.AsyncClient,
    dp: DiscoveredPage,
) -> list[TestResult]:
    soup: BeautifulSoup | None = getattr(dp, "_soup", None)
    if not soup:
        return []

    imgs = soup.find_all("img", src=True)
    broken: list[str] = []
    missing_alt: list[str] = []

    for img in imgs:
        src = img["src"]
        if not src or src.startswith("data:"):
            continue
        full_src = src if src.startswith("http") else urljoin(dp.url + "/", src)
        try:
            resp = await client.head(full_src, follow_redirects=True, timeout=8)
            if resp.status_code >= 400:
                broken.append(full_src[:100])
        except Exception:
            broken.append(full_src[:100])
        if not img.get("alt") and img.get("alt") is None:
            missing_alt.append(src[:60])

    results: list[TestResult] = []
    results.append(TestResult(
        name="No Broken Images", category=TestCategory.BROKEN_IMAGES,
        status=TestStatus.FAILED if broken else TestStatus.PASSED,
        message=f"{len(broken)} broken image(s)" if broken else f"All {len(imgs)} images OK",
        details={"broken": broken[:10]} if broken else {"total_images": len(imgs)},
    ))
    return results


async def _check_framework(dp: DiscoveredPage) -> list[TestResult]:
    fw = dp.framework
    results: list[TestResult] = []
    results.append(TestResult(
        name="Framework Detected", category=TestCategory.FRAMEWORK,
        status=TestStatus.PASSED if fw.name != DetectedFramework.UNKNOWN else TestStatus.WARNING,
        message=f"{fw.name.value}"
                + (f" v{fw.version}" if fw.version else "")
                + (" (SSR)" if fw.is_ssr else "")
                + (" (SPA)" if fw.is_spa and not fw.is_ssr else ""),
        details={"framework": fw.name.value, "version": fw.version, "spa": fw.is_spa, "ssr": fw.is_ssr},
    ))
    if fw.features:
        results.append(TestResult(
            name="Libraries & Features", category=TestCategory.FRAMEWORK,
            status=TestStatus.PASSED,
            message=", ".join(fw.features),
            details={"features": fw.features},
        ))
    return results


# ── Main lite runner ──────────────────────────────────────────────────────────
class LiteTestRunner:
    """
    Browser-free test runner using httpx + BeautifulSoup.
    Memory footprint: ~50-80 MB (vs 350+ MB with Chromium).
    """

    def __init__(
        self,
        base_url: str,
        max_pages: int = 5,
        max_depth: int = 2,
        output_dir: str = "test-reports",
        timeout: int = 20000,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.output_dir = Path(output_dir)
        self.timeout = timeout / 1000  # convert ms → seconds

    def run(self) -> TestReport:
        return asyncio.run(self.run_async())

    async def run_async(self) -> TestReport:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report = TestReport(base_url=self.base_url)
        base_domain = urlparse(self.base_url).netloc

        print(f"\n{'='*60}")
        print(f"  Web Auto Tester v1.0.0  [Lite Mode — No Browser]")
        print(f"  Target: {self.base_url}")
        print(f"{'='*60}\n")
        print("[*] Lite mode active — using httpx + BeautifulSoup (~60MB RAM)")

        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            verify=False,
        ) as client:
            # Phase 1: Discovery
            print("[*] Phase 1: Discovering pages...")
            pages = await _crawl(client, self.base_url, self.max_pages, self.max_depth)
            report.discovered_urls = [p.url for p in pages]

            if pages and pages[0].framework:
                report.site_framework = pages[0].framework

            fw_label = report.site_framework.name.value
            print(f"    Framework: {fw_label}"
                  + (f" v{report.site_framework.version}" if report.site_framework.version else ""))
            print(f"    Found {len(pages)} page(s):")
            for dp in pages:
                fw_tag = f" [{dp.framework.name.value}]" if dp.framework.name.value != "Unknown / Static HTML" else ""
                print(f"      {dp.status_code} {dp.url} - {dp.title}{fw_tag}")

            ANALYZERS = [
                ("Page Load & Performance", _check_page_load),
                ("Security Headers", _check_security_headers),
                ("SEO Basics", _check_seo),
                ("Accessibility", _check_accessibility),
                ("Framework Health", _check_framework),
            ]

            print(f"\n[*] Phase 2: Running {len(ANALYZERS)} test suites across {len(pages)} page(s)...\n")

            for idx, dp in enumerate(pages, 1):
                pr = PageResult(page=dp)
                print(f"  [{idx}/{len(pages)}] {dp.url}")

                # Run non-network analyzers
                for name, fn in ANALYZERS:
                    try:
                        if fn in (_check_page_load, _check_security_headers, _check_seo,
                                  _check_accessibility, _check_framework):
                            results = await fn(dp)
                        else:
                            results = await fn(client, dp, base_domain)
                        pr.tests.extend(results)
                        p = sum(1 for r in results if r.status == TestStatus.PASSED)
                        f = sum(1 for r in results if r.status == TestStatus.FAILED)
                        w = sum(1 for r in results if r.status == TestStatus.WARNING)
                        icon = "\033[32m+\033[0m" if f == 0 and w == 0 else "\033[33m~\033[0m" if f == 0 else "\033[31m!\033[0m"
                        print(f"    {icon} {name}: {p}P/{f}F/{w}W")
                    except Exception as e:
                        print(f"    \033[31m!\033[0m {name}: ERROR - {e}")

                # Link + image checks (need client + base_domain)
                for name, fn in [("Broken Links", _check_broken_links), ("Broken Images", _check_broken_images)]:
                    try:
                        if name == "Broken Links":
                            results = await fn(client, dp, base_domain)
                        else:
                            results = await fn(client, dp)
                        pr.tests.extend(results)
                        p = sum(1 for r in results if r.status == TestStatus.PASSED)
                        f = sum(1 for r in results if r.status == TestStatus.FAILED)
                        w = sum(1 for r in results if r.status == TestStatus.WARNING)
                        icon = "\033[32m+\033[0m" if f == 0 and w == 0 else "\033[33m~\033[0m" if f == 0 else "\033[31m!\033[0m"
                        print(f"    {icon} {name}: {p}P/{f}F/{w}W")
                    except Exception as e:
                        print(f"    \033[31m!\033[0m {name}: ERROR - {e}")

                report.pages.append(pr)
                print(f"    => {pr.passed}P / {pr.failed}F / {pr.warnings}W\n")

                # Free HTML/soup from memory between pages
                if hasattr(dp, "_html"):
                    del dp._html
                if hasattr(dp, "_soup"):
                    del dp._soup
                gc.collect()

        report.end_time = time.time()

        # Phase 3: Report
        print("[*] Phase 3: Generating report...")
        html_path = self.output_dir / "report.html"
        generate_html_report(report, str(html_path))

        json_path = self.output_dir / "report.json"
        self._write_json(report, str(json_path))

        print(f"\n{'='*60}")
        print(f"  COMPLETE  [Lite Mode]  |  {fw_label}")
        print(f"{'='*60}")
        print(f"  Pages:    {len(report.pages)}")
        print(f"  Tests:    {report.total_tests}")
        print(f"  Passed:   \033[32m{report.total_passed}\033[0m")
        print(f"  Failed:   \033[31m{report.total_failed}\033[0m")
        print(f"  Warnings: \033[33m{report.total_warnings}\033[0m")
        print(f"  Rate:     {report.pass_rate:.1f}%")
        print(f"  Time:     {report.duration_seconds:.1f}s")
        print(f"  Report:   {html_path.resolve()}")
        print(f"{'='*60}\n")

        return report

    def _write_json(self, report: TestReport, path: str) -> None:
        summary = {
            "base_url": report.base_url,
            "mode": "lite",
            "framework": report.site_framework.name.value,
            "framework_version": report.site_framework.version,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(report.start_time)),
            "duration_seconds": round(report.duration_seconds, 1),
            "total_pages": len(report.pages),
            "total_tests": report.total_tests,
            "passed": report.total_passed,
            "failed": report.total_failed,
            "warnings": report.total_warnings,
            "pass_rate": round(report.pass_rate, 1),
            "discovered_urls": report.discovered_urls,
            "pages": [
                {
                    "url": pr.page.url,
                    "title": pr.page.title,
                    "status_code": pr.page.status_code,
                    "framework": pr.page.framework.name.value,
                    "passed": pr.passed, "failed": pr.failed, "warnings": pr.warnings,
                    "tests": [
                        {
                            "name": t.name, "category": t.category.value,
                            "status": t.status.value, "message": t.message,
                            "duration_ms": round(t.duration_ms, 1),
                            "details": t.details or None,
                        }
                        for t in pr.tests
                    ],
                }
                for pr in report.pages
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
