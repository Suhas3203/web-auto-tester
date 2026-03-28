"""
CLI entry point for Web Auto Tester.

Usage:
    python -m web_auto_tester https://any-web-app.com
    python -m web_auto_tester https://example.com --max-pages 20 --headed
"""

from __future__ import annotations

import argparse
import sys

from .runner import AutoTestRunner


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="web-auto-tester",
        description=(
            "Framework-agnostic automated testing for deployed web applications. "
            "Auto-detects Angular, React, Vue, Svelte, Next.js, Nuxt, or plain HTML. "
            "Just provide a URL."
        ),
    )
    parser.add_argument(
        "url",
        help="Deployed application URL (e.g. https://your-app.com)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=30,
        help="Max pages to discover and test (default: 30)",
    )
    parser.add_argument(
        "--max-depth", type=int, default=3,
        help="Max link-following depth (default: 3)",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="Run browser in headed (visible) mode",
    )
    parser.add_argument(
        "--browser", choices=["chromium", "firefox", "webkit"], default="chromium",
        help="Browser engine (default: chromium)",
    )
    parser.add_argument(
        "--output-dir", default="test-reports",
        help="Report output directory (default: test-reports)",
    )
    parser.add_argument(
        "--no-screenshots", action="store_true",
        help="Skip full-page screenshots",
    )
    parser.add_argument(
        "--timeout", type=int, default=30000,
        help="Navigation timeout in ms (default: 30000)",
    )

    args = parser.parse_args()

    url = args.url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    runner = AutoTestRunner(
        base_url=url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        headless=not args.headed,
        browser=args.browser,
        output_dir=args.output_dir,
        screenshots=not args.no_screenshots,
        timeout=args.timeout,
    )

    report = runner.run()
    sys.exit(1 if report.total_failed > 0 else 0)


if __name__ == "__main__":
    main()
