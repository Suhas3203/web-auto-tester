"""
Test runner orchestrator - framework-agnostic.

Coordinates discovery + analysis + report generation.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from playwright.async_api import async_playwright

from .models import TestReport, PageResult, TestStatus
from .discovery import SiteCrawler
from .analyzers import ALL_ANALYZERS
from .report import generate_html_report


class AutoTestRunner:
    """
    Main entry point. Provide a URL, get a full test report.

    Usage:
        runner = AutoTestRunner("https://any-web-app.com")
        report = runner.run()
    """

    def __init__(
        self,
        base_url: str,
        max_pages: int = 30,
        max_depth: int = 3,
        headless: bool = True,
        output_dir: str = "test-reports",
        browser: str = "chromium",
        screenshots: bool = True,
        timeout: int = 30000,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.browser = browser
        self.screenshots = screenshots
        self.timeout = timeout

    def run(self) -> TestReport:
        """Synchronous entry point."""
        return asyncio.run(self.run_async())

    async def run_async(self) -> TestReport:
        """Async entry point - discovery -> analysis -> report."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ss_dir = self.output_dir / "screenshots"
        if self.screenshots:
            ss_dir.mkdir(exist_ok=True)

        report = TestReport(base_url=self.base_url)

        print(f"\n{'='*60}")
        print(f"  Web Auto Tester v1.0.0")
        print(f"  Target: {self.base_url}")
        print(f"{'='*60}\n")

        async with async_playwright() as pw:
            print(f"[*] Launching {self.browser} (headless={self.headless})...")
            browser_type = getattr(pw, self.browser)
            browser = await browser_type.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            # Phase 1: Discovery
            print("[*] Phase 1: Discovering pages...")
            crawler = SiteCrawler(
                self.base_url,
                max_pages=self.max_pages,
                max_depth=self.max_depth,
            )
            pages = await crawler.crawl(context)
            report.discovered_urls = [p.url for p in pages]

            # Determine site-level framework from first page
            if pages and pages[0].framework:
                report.site_framework = pages[0].framework

            fw_label = report.site_framework.name.value
            print(f"    Framework: {fw_label}"
                  + (f" v{report.site_framework.version}" if report.site_framework.version else ""))
            print(f"    Found {len(pages)} page(s):")
            for dp in pages:
                fw_tag = f" [{dp.framework.name.value}]" if dp.framework.name.value != "Unknown / Static HTML" else ""
                print(f"      {dp.status_code} {dp.url} - {dp.title}{fw_tag}")

            # Phase 2: Run analyzers
            print(f"\n[*] Phase 2: Running {len(ALL_ANALYZERS)} test suites "
                  f"across {len(pages)} page(s)...\n")

            for idx, dp in enumerate(pages, 1):
                pr = PageResult(page=dp)
                print(f"  [{idx}/{len(pages)}] {dp.url}")

                page = await context.new_page()
                try:
                    for name, fn in ALL_ANALYZERS:
                        try:
                            results = await fn(page, dp)
                            pr.tests.extend(results)

                            p = sum(1 for r in results if r.status == TestStatus.PASSED)
                            f = sum(1 for r in results if r.status == TestStatus.FAILED)
                            w = sum(1 for r in results if r.status == TestStatus.WARNING)

                            icon = (
                                "\033[32m+\033[0m" if f == 0 and w == 0
                                else "\033[33m~\033[0m" if f == 0
                                else "\033[31m!\033[0m"
                            )
                            print(f"    {icon} {name}: {p}P/{f}F/{w}W")

                        except Exception as e:
                            print(f"    \033[31m!\033[0m {name}: ERROR - {e}")

                    # Screenshot
                    if self.screenshots:
                        try:
                            await page.goto(dp.url, wait_until="networkidle", timeout=self.timeout)
                            await page.wait_for_timeout(1000)
                            safe = (dp.url.replace("://", "_").replace("/", "_")
                                    .replace("?", "_").replace("&", "_")[:80])
                            ss_path = ss_dir / f"{safe}.png"
                            await page.screenshot(path=str(ss_path), full_page=True)
                            if pr.tests:
                                pr.tests[0].screenshot_path = str(ss_path)
                        except Exception:
                            pass
                finally:
                    await page.close()

                report.pages.append(pr)
                print(f"    => {pr.passed}P / {pr.failed}F / {pr.warnings}W\n")

            await browser.close()

        report.end_time = time.time()

        # Phase 3: Report
        print("[*] Phase 3: Generating report...")
        html_path = self.output_dir / "report.html"
        generate_html_report(report, str(html_path))

        json_path = self.output_dir / "report.json"
        self._write_json(report, str(json_path))

        print(f"\n{'='*60}")
        print(f"  COMPLETE  |  {fw_label}")
        print(f"{'='*60}")
        print(f"  Pages:    {len(report.pages)}")
        print(f"  Tests:    {report.total_tests}")
        print(f"  Passed:   \033[32m{report.total_passed}\033[0m")
        print(f"  Failed:   \033[31m{report.total_failed}\033[0m")
        print(f"  Warnings: \033[33m{report.total_warnings}\033[0m")
        print(f"  Rate:     {report.pass_rate:.1f}%")
        print(f"  Time:     {report.duration_seconds:.1f}s")
        print(f"  Report:   {html_path.resolve()}")
        print(f"  JSON:     {json_path.resolve()}")
        print(f"{'='*60}\n")

        return report

    def _write_json(self, report: TestReport, path: str) -> None:
        summary = {
            "base_url": report.base_url,
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
