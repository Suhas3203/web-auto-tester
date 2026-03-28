"""
Web Auto Tester - Framework-agnostic automated testing for deployed web applications.

Auto-detects Angular, React, Vue, Svelte, Next.js, Nuxt, or plain HTML and
adapts its checks accordingly. Just provide a URL.

Usage:
    python -m web_auto_tester https://your-app.com
"""

from .models import TestResult, PageResult, TestReport, DetectedFramework
from .runner import AutoTestRunner

__all__ = ["AutoTestRunner", "TestResult", "PageResult", "TestReport", "DetectedFramework"]
__version__ = "1.0.0"
