"""Data models for test results - fully framework-agnostic."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class TestCategory(str, Enum):
    PAGE_LOAD = "Page Load"
    CONSOLE_ERRORS = "Console Errors"
    BROKEN_LINKS = "Broken Links"
    BROKEN_IMAGES = "Broken Images"
    FORMS = "Forms"
    PERFORMANCE = "Performance"
    ACCESSIBILITY = "Accessibility"
    FRAMEWORK = "Framework Health"
    RESPONSIVE = "Responsive Design"
    SEO = "SEO Basics"
    SECURITY_HEADERS = "Security Headers"
    NETWORK = "Network Requests"


class DetectedFramework(str, Enum):
    ANGULAR = "Angular"
    REACT = "React"
    VUE = "Vue"
    SVELTE = "Svelte"
    NEXTJS = "Next.js"
    NUXT = "Nuxt"
    GATSBY = "Gatsby"
    EMBER = "Ember"
    JQUERY = "jQuery"
    UNKNOWN = "Unknown / Static HTML"


@dataclass
class FrameworkInfo:
    """Detected framework metadata for a page."""
    name: DetectedFramework = DetectedFramework.UNKNOWN
    version: str | None = None
    is_spa: bool = False
    is_ssr: bool = False
    features: list[str] = field(default_factory=list)
    raw_signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    name: str
    category: TestCategory
    status: TestStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    screenshot_path: str | None = None


@dataclass
class DiscoveredPage:
    url: str
    title: str = ""
    status_code: int = 0
    framework: FrameworkInfo = field(default_factory=FrameworkInfo)
    depth: int = 0
    found_on: str = ""
    # Lite-runner fields (populated by httpx crawler, None in Playwright mode)
    _html: str | None = field(default=None, repr=False)
    _soup: Any | None = field(default=None, repr=False)
    _resp_headers: dict[str, str] | None = field(default=None, repr=False)
    _ttfb_ms: float = 0.0


@dataclass
class PageResult:
    page: DiscoveredPage
    tests: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.FAILED)

    @property
    def warnings(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.WARNING)


@dataclass
class TestReport:
    base_url: str
    pages: list[PageResult] = field(default_factory=list)
    site_framework: FrameworkInfo = field(default_factory=FrameworkInfo)
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    discovered_urls: list[str] = field(default_factory=list)

    @property
    def total_tests(self) -> int:
        return sum(len(p.tests) for p in self.pages)

    @property
    def total_passed(self) -> int:
        return sum(p.passed for p in self.pages)

    @property
    def total_failed(self) -> int:
        return sum(p.failed for p in self.pages)

    @property
    def total_warnings(self) -> int:
        return sum(p.warnings for p in self.pages)

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.total_passed / self.total_tests) * 100
