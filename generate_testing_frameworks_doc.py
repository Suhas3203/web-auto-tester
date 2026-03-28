#!/usr/bin/env python3
"""
Generates a comprehensive PDF document covering ALL major testing frameworks:
Playwright, Selenium, Cypress, Tosca, Puppeteer, WebDriverIO, TestCafe,
Robot Framework, Nightwatch.js, Appium, Katalon Studio, Jest + Testing Library,
k6, Detox, Gauge, Karate DSL, CodeceptJS, Watir, and Protractor.

Includes: overview, architecture, setup, code examples, pros/cons,
comparison matrix, and recommendation guide.
"""

from fpdf import FPDF
import os

# ─── Color palette ───────────────────────────────────────────────────────────
BG_DARK      = (15, 17, 23)
BG_SURFACE   = (26, 29, 39)
BG_SURFACE2  = (36, 40, 54)
BORDER_COLOR = (46, 51, 72)
TEXT_WHITE    = (225, 228, 237)
TEXT_DIM      = (139, 143, 163)
ACCENT        = (99, 102, 241)
ACCENT_LIGHT  = (129, 140, 248)
PASS_GREEN    = (34, 197, 94)
FAIL_RED      = (239, 68, 68)
WARN_YELLOW   = (245, 158, 11)

# Framework brand colors
PW_COLOR     = (45, 206, 137)   # Playwright green
SE_COLOR     = (67, 176, 42)    # Selenium green
CY_COLOR     = (36, 193, 224)   # Cypress teal
TO_COLOR     = (0, 120, 215)    # Tosca blue
PP_COLOR     = (0, 150, 136)    # Puppeteer teal
WD_COLOR     = (234, 89, 12)    # WebDriverIO orange
TC_COLOR     = (54, 179, 126)   # TestCafe green
RF_COLOR     = (0, 160, 0)      # Robot Framework green
NW_COLOR     = (236, 100, 75)   # Nightwatch orange-red
AP_COLOR     = (128, 0, 128)    # Appium purple
KS_COLOR     = (23, 162, 184)   # Katalon teal
JT_COLOR     = (198, 72, 56)    # Jest red
K6_COLOR     = (126, 58, 242)   # k6 purple
DT_COLOR     = (120, 120, 120)  # Detox gray
GA_COLOR     = (244, 168, 54)   # Gauge yellow
KA_COLOR     = (200, 50, 50)    # Karate red
CC_COLOR     = (40, 116, 166)   # CodeceptJS blue
WA_COLOR     = (0, 128, 128)    # Watir teal
PR_COLOR     = (211, 47, 47)    # Protractor red


class TestingFrameworkDoc(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 18, 18)

    # ── Header / Footer ─────────────────────────────────────────────────
    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*BG_SURFACE)
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*TEXT_DIM)
        self.set_xy(18, 3)
        self.cell(0, 6, "Testing Frameworks - Comprehensive Guide", align="L")
        self.set_xy(18, 3)
        self.cell(174, 6, f"Page {self.page_no()}", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*TEXT_DIM)
        self.cell(0, 10,
                  "Go Digital Technology Consulting LLP | March 2026 | For internal use",
                  align="C")

    # ── Helpers ──────────────────────────────────────────────────────────
    def _bg(self):
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, 210, 297, "F")

    def _section_title(self, num, title, color=ACCENT):
        self.set_fill_color(*color)
        self.rect(18, self.get_y(), 174, 1.2, "F")
        self.ln(4)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*TEXT_WHITE)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def _sub_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*ACCENT_LIGHT)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def _sub2_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*ACCENT_LIGHT)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def _body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT_WHITE)
        self.multi_cell(174, 5.5, text)
        self.ln(2)

    def _dim_body(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_DIM)
        self.multi_cell(174, 5, text)
        self.ln(2)

    def _code_block(self, code, lang=""):
        self.set_fill_color(*BG_SURFACE2)
        self.set_draw_color(*BORDER_COLOR)
        if lang:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*TEXT_DIM)
            self.cell(174, 5, f"  {lang}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_font("Courier", "", 8.5)
        self.set_text_color(200, 210, 230)
        x = self.get_x()
        y = self.get_y()
        lines = code.strip().split("\n")
        block_h = len(lines) * 4.5 + 6
        if y + block_h > 275:
            self.add_page()
            self._bg()
            y = self.get_y()
        self.set_fill_color(*BG_SURFACE2)
        self.rect(18, y, 174, block_h, "DF")
        self.set_xy(21, y + 3)
        for line in lines:
            self.cell(168, 4.5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(21)
        self.ln(4)

    def _bullet(self, text, indent=18):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT_WHITE)
        self.set_x(indent)
        self.cell(5, 5.5, "-")
        self.multi_cell(174 - (indent - 18) - 5, 5.5, text)
        self.ln(1)

    def _pros_cons(self, pros, cons):
        col_w = 85
        y_start = self.get_y()

        if y_start + 10 + max(len(pros), len(cons)) * 6 > 275:
            self.add_page()
            self._bg()
            y_start = self.get_y()

        # Pros header
        self.set_fill_color(34, 197, 94)
        self.rect(18, y_start, col_w, 7, "F")
        self.set_xy(18, y_start)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*BG_DARK)
        self.cell(col_w, 7, "  PROS", align="L")

        # Cons header
        self.set_fill_color(239, 68, 68)
        self.rect(18 + col_w + 4, y_start, col_w, 7, "F")
        self.set_xy(18 + col_w + 4, y_start)
        self.cell(col_w, 7, "  CONS", align="L")

        y = y_start + 9
        max_items = max(len(pros), len(cons))
        self.set_font("Helvetica", "", 9)

        for i in range(max_items):
            if y > 275:
                self.add_page()
                self._bg()
                y = self.get_y()

            if i < len(pros):
                self.set_text_color(*PASS_GREEN)
                self.set_xy(18, y)
                self.cell(3, 5, "+")
                self.set_text_color(*TEXT_WHITE)
                self.cell(col_w - 3, 5, f" {pros[i]}")

            if i < len(cons):
                self.set_text_color(*FAIL_RED)
                self.set_xy(18 + col_w + 4, y)
                self.cell(3, 5, "-")
                self.set_text_color(*TEXT_WHITE)
                self.cell(col_w - 3, 5, f" {cons[i]}")

            y += 6

        self.set_y(y + 4)

    def _table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [174 // len(headers)] * len(headers)

        y = self.get_y()
        needed = 8 + len(rows) * 7
        if y + needed > 275:
            self.add_page()
            self._bg()

        # Header row
        self.set_fill_color(*ACCENT)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*TEXT_WHITE)
        x = 18
        for i, h in enumerate(headers):
            self.set_xy(x, self.get_y())
            self.cell(col_widths[i], 7, f" {h}", fill=True)
            x += col_widths[i]
        self.ln(7)

        # Data rows
        self.set_font("Helvetica", "", 8.5)
        for ri, row in enumerate(rows):
            if self.get_y() > 275:
                self.add_page()
                self._bg()

            bg = BG_SURFACE if ri % 2 == 0 else BG_SURFACE2
            self.set_fill_color(*bg)
            x = 18
            for i, cell_text in enumerate(row):
                self.set_xy(x, self.get_y())
                self.set_text_color(*TEXT_WHITE)
                self.cell(col_widths[i], 7, f" {cell_text}", fill=True)
                x += col_widths[i]
            self.ln(7)

        self.ln(4)

    def _check_space(self, needed=40):
        if self.get_y() + needed > 270:
            self.add_page()
            self._bg()

    def _framework_section(self, num, name, color, description, architecture,
                           features, code_examples, pros, cons, best_for,
                           language_table=None, extra_content=None):
        """Generic framework section builder."""
        self.add_page()
        self._bg()
        self._section_title(num, name, color)
        self._body(description)

        self._sub_title(f"{num}.1 Architecture & How It Works")
        self._body(architecture)

        self._sub_title(f"{num}.2 Key Features")
        for f in features:
            self._check_space(8)
            self._bullet(f)

        if language_table:
            self._check_space(40)
            self._sub_title(f"{num}.3 Language Support")
            self._table(*language_table)

        if code_examples:
            self._check_space(30)
            self._sub_title(f"{num}.{'4' if language_table else '3'} Code Examples")
            for title, code, lang in code_examples:
                self._check_space(30)
                self._sub2_title(title)
                self._code_block(code, lang)

        if extra_content:
            extra_content(self, num)

        self._check_space(50)
        sub_n = "5" if language_table else "4"
        if code_examples and language_table:
            sub_n = "5"
        elif code_examples or language_table:
            sub_n = "4"
        else:
            sub_n = "3"
        self._sub_title(f"{num}.{sub_n} Pros & Cons")
        self._pros_cons(pros, cons)

        self._check_space(30)
        next_n = str(int(sub_n) + 1)
        self._sub_title(f"{num}.{next_n} Best Suited For")
        self._body(best_for)


def generate_doc():
    pdf = TestingFrameworkDoc()

    # ═══════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()

    # Gradient bar
    for i in range(80):
        r = int(30 + (99 - 30) * i / 80)
        g = int(27 + (102 - 27) * i / 80)
        b = int(75 + (241 - 75) * i / 80)
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 60 + i * 0.8, 210, 0.8, "F")

    # Title
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*TEXT_WHITE)
    pdf.set_xy(18, 72)
    pdf.cell(174, 18, "Testing Frameworks", align="L")
    pdf.set_xy(18, 90)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(*ACCENT_LIGHT)
    pdf.cell(174, 10, "Comprehensive Guide & Comparison", align="L")

    # Subtitle
    pdf.set_xy(18, 108)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*TEXT_DIM)
    pdf.cell(174, 6,
             "Playwright | Selenium | Cypress | Tosca | Puppeteer | WebDriverIO", align="L")
    pdf.set_xy(18, 115)
    pdf.cell(174, 6,
             "TestCafe | Robot Framework | Nightwatch.js | Appium | Katalon Studio", align="L")
    pdf.set_xy(18, 122)
    pdf.cell(174, 6,
             "Jest + Testing Library | k6 | Detox | Gauge | Karate | CodeceptJS | Watir", align="L")

    # Description
    pdf.set_xy(18, 140)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*TEXT_WHITE)
    pdf.multi_cell(174, 6.5,
        "A complete reference covering 19+ testing and automation frameworks. "
        "Includes architecture, setup, code examples, pros & cons, performance "
        "benchmarks, and a decision framework for choosing the right tool.")

    # Tags
    tags = ["Playwright", "Selenium", "Cypress", "Tosca", "Puppeteer", "WebDriverIO",
            "TestCafe", "Robot Framework", "Appium", "k6", "Jest", "E2E Testing",
            "Python", "JavaScript", "TypeScript", "Java", "CI/CD", "Performance"]
    pdf.set_xy(18, 175)
    x = 18
    for tag in tags:
        w = pdf.get_string_width(tag) + 12
        if x + w > 192:
            x = 18
            pdf.ln(9)
            pdf.set_x(18)
        pdf.set_fill_color(*ACCENT)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*TEXT_WHITE)
        pdf.set_x(x)
        pdf.cell(w, 7, tag, fill=True, align="C")
        x += w + 4

    # Footer
    pdf.set_xy(18, 260)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_DIM)
    pdf.cell(174, 6, "Version 2.0.0  |  March 2026  |  Go Digital Technology Consulting LLP",
             align="L")

    # ═══════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*TEXT_WHITE)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    toc = [
        ("1", "Overview & Testing Landscape"),
        ("2", "Playwright"),
        ("3", "Selenium WebDriver"),
        ("4", "Cypress"),
        ("5", "Tricentis Tosca"),
        ("6", "Puppeteer"),
        ("7", "WebDriverIO"),
        ("8", "TestCafe"),
        ("9", "Robot Framework"),
        ("10", "Nightwatch.js"),
        ("11", "Appium"),
        ("12", "Katalon Studio"),
        ("13", "Jest + Testing Library"),
        ("14", "k6 (Performance Testing)"),
        ("15", "Detox (React Native)"),
        ("16", "Gauge"),
        ("17", "Karate DSL"),
        ("18", "CodeceptJS"),
        ("19", "Watir"),
        ("20", "Protractor (Deprecated)"),
        ("21", "Head-to-Head Comparison"),
        ("22", "Setup & Quick Start Guide"),
        ("23", "CI/CD Integration Patterns"),
        ("24", "Decision Framework"),
        ("25", "Glossary & Resources"),
    ]

    for num, title in toc:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*TEXT_WHITE)
        pdf.cell(12, 7, num)
        pdf.cell(150, 7, title)
        pdf.ln(7)
        pdf.set_draw_color(*BORDER_COLOR)
        y = pdf.get_y() - 3
        pdf.dashed_line(30, y, 192, y, 1, 2)
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf._bg()

    # ═══════════════════════════════════════════════════════════════════
    # 1. OVERVIEW & LANDSCAPE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("1", "Overview & Testing Landscape")

    pdf._body(
        "End-to-end (E2E) testing validates that an application works correctly from the user's "
        "perspective by automating browser interactions. The testing framework landscape has evolved "
        "significantly - from Selenium's dominance since 2004 to modern alternatives like Playwright "
        "and Cypress that address long-standing pain points around flakiness, speed, and developer "
        "experience. Today, there are 19+ major frameworks covering browser E2E, mobile, API, "
        "performance, and component testing."
    )

    pdf._sub_title("1.1 Framework Categories")
    pdf._table(
        ["Category", "Frameworks", "Primary Use"],
        [
            ["Browser E2E", "Playwright, Selenium, Cypress, Puppeteer", "Web app end-to-end tests"],
            ["Browser E2E", "WebDriverIO, TestCafe, Nightwatch, CodeceptJS", "Web app end-to-end tests"],
            ["Enterprise", "Tosca, Katalon Studio", "Scriptless/low-code testing"],
            ["Mobile", "Appium, Detox", "Native/hybrid mobile apps"],
            ["API/Contract", "Karate DSL", "REST/GraphQL API testing"],
            ["Performance", "k6", "Load & stress testing"],
            ["Component/Unit", "Jest + Testing Library", "Component & unit tests"],
            ["BDD/Acceptance", "Gauge, Robot Framework", "Behavior-driven testing"],
            ["Legacy", "Protractor, Watir", "Deprecated / niche"],
        ],
        [34, 80, 60],
    )

    pdf._sub_title("1.2 Testing Pyramid Context")
    pdf._body(
        "E2E tests sit at the top of the testing pyramid. They provide the highest confidence but "
        "are the slowest and most expensive to maintain. Best practice is:\n"
        "- Unit tests: 70-80% (fast, isolated) - Jest, Vitest, pytest\n"
        "- Integration tests: 15-20% (API/service level) - Karate, Supertest\n"
        "- E2E tests: 5-10% (critical user journeys) - Playwright, Cypress, Selenium\n"
        "- Performance tests: As needed - k6, Artillery\n"
        "- Mobile tests: As needed - Appium, Detox"
    )

    pdf._sub_title("1.3 Key Selection Criteria")
    pdf._body(
        "When evaluating a testing framework, consider these dimensions:\n\n"
        "- Browser Coverage: Which browsers must you support?\n"
        "- Language Ecosystem: What does your team already know?\n"
        "- Speed & Parallelism: How fast can tests run in CI?\n"
        "- Debugging Experience: How easy is it to diagnose failures?\n"
        "- Flakiness: How reliable are tests without manual waits?\n"
        "- Cross-domain/iFrame: Does your app use these?\n"
        "- Mobile Testing: Do you need native mobile support?\n"
        "- Cost: Open-source vs. licensed?\n"
        "- Community & Ecosystem: Plugins, docs, hiring pool?\n"
        "- API Testing: Do you need API + UI in one tool?"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 2. PLAYWRIGHT
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("2", "Playwright", PW_COLOR)

    pdf._body(
        "Playwright is an open-source browser automation framework by Microsoft, released in 2020. "
        "It was built by the same team behind Puppeteer and designed to solve Puppeteer's limitations "
        "(single-browser, no auto-wait). Playwright controls Chromium, Firefox, and WebKit through "
        "a single API, using direct browser protocol connections (CDP for Chromium, custom protocols "
        "for Firefox/WebKit) rather than an intermediary driver."
    )

    pdf._sub_title("2.1 Architecture")
    pdf._body(
        "Playwright uses a client-server architecture where your test code (the client) communicates "
        "with browser instances through WebSocket connections to a Playwright Server process. This "
        "server speaks the native protocol of each browser:\n\n"
        "  Test Code  -->  Playwright Server  -->  CDP (Chromium)\n"
        "                                     -->  Firefox Protocol\n"
        "                                     -->  WebKit Protocol\n\n"
        "Key architectural advantages:\n"
        "- No HTTP overhead (unlike Selenium's JSON Wire)\n"
        "- Direct browser process control = faster command execution\n"
        "- Browser contexts (isolated, parallel) share a single browser process\n"
        "- Each context gets its own cookies, storage, and permissions"
    )

    pdf._sub_title("2.2 Key Features")
    features_pw = [
        "Auto-wait: Every action auto-waits for elements to be actionable (visible, stable, enabled)",
        "Multi-browser: Chromium, Firefox, WebKit from one API",
        "Browser Contexts: Lightweight isolated sessions - faster than launching new browsers",
        "Network Interception: Native route() API for mocking, stubbing, and recording HAR files",
        "Tracing: Built-in trace viewer with DOM snapshots, network, console logs, and screenshots",
        "Codegen: Record user actions and generate test code automatically",
        "Component Testing: Test React/Vue/Svelte components in real browsers",
        "API Testing: Built-in request context for REST API testing alongside UI tests",
        "Visual Comparisons: Pixel-level screenshot diffing with toHaveScreenshot()",
        "Parallelism: Fully parallel execution with worker-based sharding out of the box",
        "Mobile Emulation: Device profiles for viewport, user agent, touch, and geolocation",
        "Multi-tab & Multi-origin: First-class support for popup windows and cross-origin iframes",
    ]
    for f in features_pw:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(60)
    pdf._sub_title("2.3 Language Support")
    pdf._table(
        ["Language", "Package", "Test Runner", "Maturity"],
        [
            ["JavaScript/TS", "@playwright/test", "Built-in (Playwright Test)", "Primary"],
            ["Python", "playwright (pip)", "pytest-playwright", "Official"],
            ["Java", "com.microsoft.playwright", "JUnit / TestNG", "Official"],
            ["C# / .NET", "Microsoft.Playwright", "NUnit / MSTest", "Official"],
        ],
        [32, 45, 52, 45],
    )

    pdf.add_page()
    pdf._bg()
    pdf._sub_title("2.4 Code Examples")

    pdf._sub2_title("TypeScript (Playwright Test)")
    pdf._code_block("""
import { test, expect } from '@playwright/test';

test('user can search products', async ({ page }) => {
  await page.goto('https://myapp.com');
  await page.fill('[data-testid="search"]', 'laptop');
  await page.click('[data-testid="search-btn"]');

  await expect(page.locator('.product-card')).toHaveCount(5);
  await expect(page).toHaveURL(/search\\?q=laptop/);
});
""", "typescript")

    pdf._sub2_title("Python (pytest)")
    pdf._code_block("""
from playwright.sync_api import Page, expect

def test_search_products(page: Page):
    page.goto("https://myapp.com")
    page.fill('[data-testid="search"]', 'laptop')
    page.click('[data-testid="search-btn"]')

    expect(page.locator(".product-card")).to_have_count(5)
""", "python")

    pdf._check_space(50)
    pdf._sub_title("2.5 Configuration")
    pdf._code_block("""
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : '50%',
  reporter: [['html'], ['junit', { outputFile: 'results.xml' }]],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit',   use: { ...devices['Desktop Safari'] } },
  ],
});
""", "typescript")

    pdf._check_space(50)
    pdf._sub_title("2.6 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Fastest execution - direct browser protocol",
            "True cross-browser (Chromium, Firefox, WebKit)",
            "Auto-wait eliminates most flakiness",
            "Built-in trace viewer is best-in-class debugging",
            "4 official languages (JS, Python, Java, C#)",
            "Network interception + HAR replay native",
            "Parallel execution out of the box",
            "Free and open source (Apache 2.0)",
            "Active development by Microsoft",
        ],
        cons=[
            "Relatively newer (2020) - smaller community than Selenium",
            "No IE11 support (by design)",
            "Browser binaries downloaded separately (~400MB)",
            "Less 3rd-party plugin ecosystem than Cypress",
            "No native mobile app testing (only emulation)",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("2.7 Best Suited For")
    pdf._body(
        "- New projects choosing a testing framework from scratch\n"
        "- Teams needing true cross-browser testing (including Safari/WebKit)\n"
        "- Python, Java, or C# shops wanting first-class E2E support\n"
        "- Applications with complex network interactions (API mocking)\n"
        "- CI/CD pipelines needing fast, parallel, reliable tests"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 3. SELENIUM
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("3", "Selenium WebDriver", SE_COLOR)

    pdf._body(
        "Selenium is the oldest and most widely adopted browser automation framework, originally "
        "created in 2004 by Jason Huggins at ThoughtWorks. Selenium WebDriver (v2+) became a W3C "
        "standard in 2018, making it the only testing tool backed by an official web standard. "
        "Selenium 4 (2021) added relative locators, Chrome DevTools Protocol access, and improved "
        "the Selenium Grid for distributed testing."
    )

    pdf._sub_title("3.1 Architecture")
    pdf._body(
        "Selenium uses a client-server architecture with the W3C WebDriver protocol:\n\n"
        "  Test Code --> Language Binding --> HTTP/JSON Wire --> Browser Driver --> Browser\n\n"
        "Each browser requires its own driver executable. Selenium 4 introduced Selenium Manager "
        "to auto-manage driver binaries.\n\n"
        "Components:\n"
        "- WebDriver API: The standard interface your tests call\n"
        "- Browser Drivers: chromedriver, geckodriver, msedgedriver, safaridriver\n"
        "- Selenium Grid: Distributed execution across multiple machines\n"
        "- Selenium IDE: Browser extension for record-and-playback\n"
        "- Selenium Manager: Auto-downloads matching driver versions (4.6+)"
    )

    pdf._sub_title("3.2 Key Features")
    features_se = [
        "W3C Standard: Only framework backed by an official web standard",
        "Language Support: Java, Python, C#, Ruby, JavaScript, Kotlin - widest coverage",
        "Selenium Grid: Distribute tests across machines, browsers, and OS versions",
        "Real Browsers: Tests run in actual browser processes, not emulated",
        "Cross-platform: Windows, macOS, Linux, Docker, cloud grids",
        "Selenium IDE: Record tests in Chrome/Firefox extension, export to code",
        "BiDi Protocol: Selenium 4 adds Chrome DevTools Protocol for network/console",
        "Selenium Manager: Auto-manages browser driver versions",
        "Mature Ecosystem: Huge library of plugins, wrappers, and community tools",
        "Legacy Support: Can test IE11, older Edge, and legacy browsers",
    ]
    for f in features_se:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(60)
    pdf._sub_title("3.3 Language Support")
    pdf._table(
        ["Language", "Package", "Driver Mgmt", "Maturity"],
        [
            ["Java", "selenium-java", "Selenium Manager", "Primary"],
            ["Python", "selenium (pip)", "Selenium Manager", "Primary"],
            ["C# / .NET", "Selenium.WebDriver (NuGet)", "Selenium Manager", "Primary"],
            ["Ruby", "selenium-webdriver (gem)", "Selenium Manager", "Primary"],
            ["JavaScript", "selenium-webdriver (npm)", "Selenium Manager", "Official"],
        ],
        [30, 48, 52, 44],
    )

    pdf.add_page()
    pdf._bg()
    pdf._sub_title("3.4 Code Examples")

    pdf._sub2_title("Python (with pytest)")
    pdf._code_block("""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_search_products():
    driver = webdriver.Chrome()
    try:
        driver.get("https://myapp.com")
        search = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="search"]'))
        )
        search.send_keys("laptop")
        driver.find_element(By.CSS_SELECTOR, '[data-testid="search-btn"]').click()
        cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-card"))
        )
        assert len(cards) == 5
    finally:
        driver.quit()
""", "python")

    pdf._sub2_title("Java (JUnit 5)")
    pdf._code_block("""
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.*;
import org.junit.jupiter.api.*;

class ProductSearchTest {
    WebDriver driver;

    @BeforeEach
    void setup() { driver = new ChromeDriver(); }

    @AfterEach
    void teardown() { driver.quit(); }

    @Test
    void userCanSearch() {
        driver.get("https://myapp.com");
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.visibilityOfElementLocated(
            By.cssSelector("[data-testid='search']")
        )).sendKeys("laptop");
        driver.findElement(By.cssSelector("[data-testid='search-btn']")).click();
    }
}
""", "java")

    pdf._check_space(50)
    pdf._sub_title("3.5 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "W3C standard - vendor-neutral, future-proof",
            "Widest language support (6+ languages)",
            "Largest community, most tutorials, biggest hiring pool",
            "Selenium Grid for distributed execution",
            "Cloud grid services (BrowserStack, Sauce Labs)",
            "IE11 and legacy browser support",
            "Mature and battle-tested over 20 years",
        ],
        cons=[
            "No built-in auto-wait (must use explicit waits)",
            "Slower than Playwright (HTTP protocol overhead)",
            "Flakiness is the #1 complaint (timing issues)",
            "No native network interception (needs proxy)",
            "No built-in test runner or assertions",
            "More verbose code than modern alternatives",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("3.6 Best Suited For")
    pdf._body(
        "- Enterprise teams with existing Selenium infrastructure\n"
        "- Projects requiring IE11 or legacy browser support\n"
        "- Teams using Java, Ruby, or C# as primary languages\n"
        "- Organizations using cloud grid providers\n"
        "- Projects needing cross-platform at scale with Selenium Grid"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 4. CYPRESS
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("4", "Cypress", CY_COLOR)

    pdf._body(
        "Cypress is a JavaScript-based end-to-end testing framework that runs directly inside the "
        "browser. Released in 2017, it was designed to address the flakiness and complexity of "
        "Selenium-based testing. Cypress is particularly popular in the React and frontend developer "
        "community for its excellent developer experience, time-travel debugging, and automatic waiting."
    )

    pdf._sub_title("4.1 Architecture")
    pdf._body(
        "Unlike Selenium and Playwright which control browsers from outside, Cypress runs inside "
        "the browser alongside your application:\n\n"
        "  +---------------------------+\n"
        "  |  Browser Process          |\n"
        "  |  +--------+ +---------+  |\n"
        "  |  | Cypress | | Your    |  |\n"
        "  |  | Test    | | App     |  |\n"
        "  |  | Runner  | | (iframe)|  |\n"
        "  |  +--------+ +---------+  |\n"
        "  +---------------------------+\n"
        "        |            |\n"
        "    Node.js Server (proxy, file system, DB access)\n\n"
        "This gives Cypress direct access to the DOM, network layer, and browser APIs. "
        "The trade-off is it runs in a single browser tab with cross-origin limitations."
    )

    pdf._sub_title("4.2 Key Features")
    features_cy = [
        "Time-Travel Debugging: DOM snapshots at every command",
        "Automatic Waiting: Commands auto-retry until assertions pass",
        "Real-time Reloading: Tests re-run automatically when you save files",
        "Network Stubbing: cy.intercept() for mocking API responses inline",
        "Screenshot & Video: Automatic screenshots on failure, full video recording",
        "Cypress Dashboard: Cloud service for analytics and parallelization",
        "Component Testing: Test React, Vue, Angular, Svelte components in isolation",
        "Retry-ability: Built-in assertion retry with configurable timeouts",
        "Spies & Stubs: Built-in Sinon.js for function spying and stubbing",
    ]
    for f in features_cy:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf.add_page()
    pdf._bg()
    pdf._sub_title("4.3 Code Examples")

    pdf._sub2_title("Basic E2E Test")
    pdf._code_block("""
describe('Product Search', () => {
  it('should find products', () => {
    cy.visit('https://myapp.com');
    cy.get('[data-testid="search"]').type('laptop');
    cy.get('[data-testid="search-btn"]').click();
    cy.get('.product-card').should('have.length', 5);
    cy.url().should('include', 'search?q=laptop');
  });
});
""", "javascript")

    pdf._sub2_title("API Mocking")
    pdf._code_block("""
it('handles API errors', () => {
  cy.intercept('GET', '/api/products', {
    statusCode: 500,
    body: { error: 'Database unavailable' }
  }).as('getProducts');

  cy.visit('/products');
  cy.wait('@getProducts');
  cy.get('.error-banner').should('be.visible');
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("4.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Best-in-class developer experience (DX)",
            "Time-travel debugging is unique and powerful",
            "Automatic waiting + retry - very low flakiness",
            "Built-in mocking, spies, stubs (Sinon.js)",
            "Excellent documentation and tutorials",
            "Component testing for React/Vue/Angular/Svelte",
            "Large plugin ecosystem (700+ plugins)",
        ],
        cons=[
            "JavaScript/TypeScript only - no Python, Java, C#",
            "Limited multi-tab support",
            "Cross-origin restrictions (relaxed in v12 but limited)",
            "No native parallel execution (needs Cypress Cloud)",
            "No true Safari/WebKit support (experimental only)",
            "Cypress Cloud is paid for advanced features",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("4.5 Best Suited For")
    pdf._body(
        "- Frontend-heavy teams (React, Vue, Angular) using JavaScript/TypeScript\n"
        "- Projects prioritizing developer experience and fast iteration\n"
        "- Applications that need extensive API mocking in tests\n"
        "- Teams wanting component-level testing alongside E2E"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 5. TOSCA
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("5", "Tricentis Tosca", TO_COLOR)

    pdf._body(
        "Tricentis Tosca is an enterprise-grade, scriptless (no-code/low-code) test automation "
        "platform. Unlike code-first tools, Tosca uses a model-based testing approach where testers "
        "define tests using UI models, reusable modules, and data-driven configurations. Designed "
        "for large enterprises with complex application landscapes including web, desktop, mobile, "
        "API, and SAP testing."
    )

    pdf._sub_title("5.1 Architecture & Workflow")
    pdf._body(
        "Tosca uses a proprietary architecture with these components:\n\n"
        "- Tosca Commander: Central IDE for test design, execution, and management\n"
        "- Module Scanner: Scans application UIs to build technical models\n"
        "- Test Case Designer: Visual editor to assemble test steps from modules\n"
        "- Execution Engine: Runs tests on local machines or distributed agents (DEX)\n"
        "- Test Data Service (TDS): Centralized test data management\n"
        "- Reporting & Analytics: Built-in dashboards and CI/CD integration\n\n"
        "Workflow: SCAN (capture UI) -> BUILD (drag-drop modules) -> DATA (connect test data) "
        "-> EXECUTE (run via Commander/DEX) -> REPORT (review dashboards)"
    )

    pdf._sub_title("5.2 Key Features")
    features_to = [
        "Model-Based Testing: Build tests from UI/API models, not scripts",
        "Scriptless / No-Code: QA testers without coding skills can create tests",
        "Multi-technology: Web, Desktop, Mobile, SAP, Salesforce, API, Mainframe",
        "Risk-Based Testing: Prioritize tests based on business risk analysis",
        "Test Data Service: Synthetic test data generation and management",
        "Distributed Execution (DEX): Run tests across multiple agents",
        "SAP Specialization: Deep SAP integration (S/4HANA, Fiori, GUI)",
        "AI-powered: Self-healing selectors, intelligent test maintenance",
        "Compliance: Audit trails, version control, regulatory compliance",
    ]
    for f in features_to:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(50)
    pdf._sub_title("5.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "No coding required - accessible to manual QA testers",
            "Multi-technology (Web, Desktop, Mobile, SAP, API)",
            "Model-based approach = high test reusability",
            "AI-powered self-healing reduces maintenance",
            "Enterprise-grade: audit trails, compliance",
            "Best-in-class SAP testing capabilities",
            "Vendor support with SLAs",
        ],
        cons=[
            "Expensive licensing ($30K-$100K+ per year)",
            "Vendor lock-in (proprietary, not portable)",
            "Less flexible than code-based frameworks",
            "Slower test execution than Playwright/Cypress",
            "Limited community resources vs open-source",
            "Not ideal for developer-led testing culture",
            "Overkill for small/medium projects",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("5.4 Best Suited For")
    pdf._body(
        "- Large enterprises with complex application landscapes\n"
        "- Organizations with SAP/Salesforce/Mainframe systems\n"
        "- QA teams without strong coding skills\n"
        "- Regulated industries needing audit trails and compliance\n"
        "- Enterprises willing to invest in licensed tooling"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 6. PUPPETEER
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("6", "Puppeteer", PP_COLOR)

    pdf._body(
        "Puppeteer is a Node.js library by Google that provides a high-level API to control "
        "Chromium-based browsers via the Chrome DevTools Protocol (CDP). Released in 2017, it was "
        "the spiritual predecessor to Playwright. Puppeteer excels at browser automation tasks like "
        "web scraping, PDF generation, screenshot capture, and performance profiling, in addition "
        "to testing."
    )

    pdf._sub_title("6.1 Architecture")
    pdf._body(
        "Puppeteer communicates directly with the browser via the Chrome DevTools Protocol "
        "over a WebSocket connection:\n\n"
        "  Node.js Script --> WebSocket --> CDP --> Chromium/Chrome/Firefox\n\n"
        "Key points:\n"
        "- Direct CDP access gives fine-grained browser control\n"
        "- No intermediary driver process (unlike Selenium)\n"
        "- Bundles a compatible Chromium binary automatically\n"
        "- Firefox support added experimentally via WebDriver BiDi\n"
        "- No Safari/WebKit support (use Playwright for that)"
    )

    pdf._sub_title("6.2 Key Features")
    for f in [
        "Chrome DevTools Protocol: Direct, low-level browser control",
        "PDF Generation: High-quality PDF rendering from web pages",
        "Screenshot Capture: Full-page and element-level screenshots",
        "Network Interception: Monitor and modify network requests/responses",
        "Performance Profiling: Access Chrome's performance tracing",
        "Web Scraping: Navigate and extract data from dynamic SPAs",
        "Code Coverage: JavaScript and CSS code coverage collection",
        "Headless Mode: New headless mode in Chrome 112+ (not old headless)",
        "Auto-downloaded Browser: Ships with matching Chromium binary",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("6.3 Code Example")
    pdf._code_block("""
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  await page.goto('https://myapp.com');
  await page.type('#search', 'laptop');
  await page.click('#search-btn');

  await page.waitForSelector('.product-card');
  const count = await page.$$eval('.product-card', els => els.length);
  console.assert(count === 5, 'Expected 5 products');

  await page.screenshot({ path: 'results.png' });
  await browser.close();
})();
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("6.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Direct CDP access - most powerful Chromium control",
            "Excellent for scraping, PDFs, screenshots",
            "Bundled Chromium - zero driver management",
            "Performance profiling built-in",
            "Lightweight - smaller API surface than Playwright",
            "Backed by Google Chrome team",
            "Large community and ecosystem",
        ],
        cons=[
            "Chromium-only (no Firefox/Safari in stable)",
            "No built-in auto-wait (must write manual waits)",
            "No built-in test runner or assertions",
            "JavaScript/TypeScript only",
            "No parallel execution built-in",
            "Being superseded by Playwright for testing use cases",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("6.5 Best Suited For")
    pdf._body(
        "- Web scraping and data extraction from SPAs\n"
        "- PDF generation from web pages\n"
        "- Performance profiling and monitoring\n"
        "- Chromium-specific browser automation\n"
        "- Teams already invested in Puppeteer that don't need multi-browser"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 7. WEBDRIVERIO
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("7", "WebDriverIO", WD_COLOR)

    pdf._body(
        "WebDriverIO (WDIO) is a progressive automation framework for Node.js built on top of "
        "the WebDriver protocol (and optionally Chrome DevTools Protocol). It combines the "
        "standardization of WebDriver with modern developer experience features. WDIO supports "
        "web, mobile (via Appium), and desktop testing from a single framework."
    )

    pdf._sub_title("7.1 Architecture")
    pdf._body(
        "WDIO acts as a test runner and WebDriver client combined:\n\n"
        "  WDIO Test Runner --> WebDriver Protocol --> Browser Driver --> Browser\n"
        "                  --> DevTools Protocol --> Chrome/Edge (alternative)\n"
        "                  --> Appium --> Mobile Device\n\n"
        "WDIO v8 supports both protocols, letting you choose WebDriver for compatibility "
        "or DevTools for speed. It includes a built-in test runner with worker-based "
        "parallelism, reporters, and service integrations."
    )

    pdf._sub_title("7.2 Key Features")
    for f in [
        "Dual Protocol: WebDriver (W3C) and DevTools Protocol support",
        "Built-in Test Runner: Parallel execution with workers, retries, reporters",
        "Mobile Testing: First-class Appium integration for iOS/Android",
        "Page Object Pattern: Built-in support with $ and $$ selectors",
        "Framework Agnostic: Works with Mocha, Jasmine, or Cucumber",
        "Service Plugins: 50+ community services (visual testing, Appium, etc.)",
        "Component Testing: React, Vue, Svelte, Lit, Stencil components",
        "Auto-wait: Implicit waiting built into commands",
        "Cross-browser: Chrome, Firefox, Safari, Edge via WebDriver",
        "Cloud Integration: BrowserStack, Sauce Labs, LambdaTest built-in",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("7.3 Code Example")
    pdf._code_block("""
describe('Product Search', () => {
  it('should find products', async () => {
    await browser.url('https://myapp.com');
    await $('[data-testid="search"]').setValue('laptop');
    await $('[data-testid="search-btn"]').click();

    const cards = await $$('.product-card');
    await expect(cards).toBeElementsArrayOfSize(5);
  });
});
""", "javascript (mocha)")

    pdf._code_block("""
// wdio.conf.js
exports.config = {
  runner: 'local',
  specs: ['./test/specs/**/*.js'],
  maxInstances: 5,
  capabilities: [{ browserName: 'chrome' }],
  framework: 'mocha',
  reporters: ['spec', ['allure', { outputDir: 'allure-results' }]],
  services: ['chromedriver'],
};
""", "javascript (config)")

    pdf._check_space(50)
    pdf._sub_title("7.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Dual protocol (WebDriver + DevTools) flexibility",
            "Built-in mobile testing via Appium service",
            "Excellent plugin/service ecosystem",
            "BDD support via Cucumber integration",
            "Cloud grid services built-in",
            "Active community, frequent releases",
            "Component testing support",
        ],
        cons=[
            "JavaScript/TypeScript only",
            "Complex configuration (many moving parts)",
            "Slower than Playwright for pure browser tests",
            "Documentation can be overwhelming",
            "Debugging is less polished than Cypress/Playwright",
            "WebDriver protocol inherits Selenium's flakiness",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("7.5 Best Suited For")
    pdf._body(
        "- Teams needing web + mobile testing in one framework\n"
        "- Projects using BDD/Cucumber for acceptance tests\n"
        "- Organizations using cloud grid providers\n"
        "- Teams wanting WebDriver standard compliance with modern DX"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 8. TESTCAFE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("8", "TestCafe", TC_COLOR)

    pdf._body(
        "TestCafe is an open-source Node.js E2E testing framework by DevExpress. Its unique "
        "selling point is zero configuration and no WebDriver dependency - it injects test scripts "
        "directly into web pages via a URL-rewriting proxy. This means it works with any browser "
        "that can open a URL, including remote devices and cloud browsers."
    )

    pdf._sub_title("8.1 Architecture")
    pdf._body(
        "TestCafe uses a reverse proxy architecture:\n\n"
        "  TestCafe Proxy Server --> Injects test scripts --> Browser loads page via proxy\n\n"
        "- No WebDriver or browser driver needed\n"
        "- Works by rewriting page URLs through its proxy\n"
        "- Injects driver scripts alongside your app in the browser\n"
        "- Supports any browser that can navigate to a URL\n"
        "- Built-in test runner with parallel execution across browsers"
    )

    pdf._sub_title("8.2 Key Features")
    for f in [
        "Zero Config: No WebDriver, no browser plugins, no native modules",
        "Any Browser: Works with Chrome, Firefox, Safari, Edge, IE, even remote mobile",
        "Auto-wait: Smart assertion mechanism that auto-retries",
        "Concurrent Testing: Run tests in multiple browsers simultaneously",
        "Role-based Auth: Built-in role management for login state reuse",
        "Request Mocking: Built-in HTTP request/response mocking",
        "Screenshots & Video: Capture on failure or at any point",
        "Page Object Model: First-class Page Model support",
        "TypeScript: Native TypeScript support out of the box",
        "Live Mode: Watch mode with instant re-runs on file changes",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("8.3 Code Example")
    pdf._code_block("""
import { Selector } from 'testcafe';

fixture('Product Search')
  .page('https://myapp.com');

test('should find products', async t => {
  await t
    .typeText('[data-testid="search"]', 'laptop')
    .click('[data-testid="search-btn"]')
    .expect(Selector('.product-card').count)
    .eql(5);
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("8.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Zero setup - no drivers, no plugins",
            "Works with ANY browser (even remote/mobile)",
            "Built-in auto-wait and assertion retry",
            "Concurrent multi-browser testing",
            "Role-based authentication built-in",
            "Native TypeScript support",
            "Free and open source",
        ],
        cons=[
            "JavaScript/TypeScript only",
            "Proxy architecture can cause subtle issues",
            "Slower than Playwright for complex tests",
            "Smaller community than Cypress/Playwright",
            "Less plugin ecosystem",
            "No component testing",
            "DevExpress shifting focus (uncertain future)",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("8.5 Best Suited For")
    pdf._body(
        "- Teams wanting zero-config E2E testing\n"
        "- Projects needing to test across many browsers including mobile\n"
        "- Teams that want built-in role/auth management\n"
        "- Quick-start E2E testing without complex setup"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 9. ROBOT FRAMEWORK
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("9", "Robot Framework", RF_COLOR)

    pdf._body(
        "Robot Framework is a generic open-source automation framework for acceptance testing "
        "and robotic process automation (RPA). Originally developed at Nokia Networks (2005), "
        "it uses a keyword-driven testing approach with a tabular test data syntax. Robot Framework "
        "is written in Python and can be extended with libraries for web (SeleniumLibrary, Browser), "
        "API, database, SSH, and more."
    )

    pdf._sub_title("9.1 Architecture")
    pdf._body(
        "Robot Framework follows a layered architecture:\n\n"
        "  Test Cases (.robot files) --> Robot Framework Core --> Libraries --> System Under Test\n\n"
        "- Test data is written in tabular format (.robot files)\n"
        "- Keywords abstract test actions (can be built-in, library, or user-defined)\n"
        "- Libraries provide the actual implementation (Selenium, Browser, REST, etc.)\n"
        "- Extensible via Python or Java libraries\n"
        "- Built-in HTML/XML reporting with log files"
    )

    pdf._sub_title("9.2 Key Features")
    for f in [
        "Keyword-Driven: Human-readable test cases using keywords",
        "Extensible: 400+ libraries on RobotFramework.org",
        "Multi-domain: Web, API, Desktop, Database, SSH, RPA",
        "Tabular Syntax: Easy for non-programmers to read and write",
        "BDD Support: Given/When/Then style test cases",
        "Tagging: Tag tests for selective execution and reporting",
        "Variables: Support for scalar, list, and dictionary variables",
        "Listeners: Hook into test execution events",
        "Parallel Execution: Via Pabot (parallel robot framework)",
        "Built-in Reports: HTML report and log generation",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("9.3 Code Example")
    pdf._code_block("""
*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${URL}     https://myapp.com

*** Test Cases ***
User Can Search Products
    Open Browser    ${URL}    chrome
    Input Text      [data-testid="search"]    laptop
    Click Button    [data-testid="search-btn"]
    Wait Until Element Is Visible    css:.product-card
    ${count}=    Get Element Count    css:.product-card
    Should Be Equal As Numbers    ${count}    5
    [Teardown]    Close Browser
""", "robot")

    pdf._check_space(50)
    pdf._sub_title("9.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Keyword-driven: readable by non-technical stakeholders",
            "Highly extensible (400+ libraries)",
            "Multi-domain testing (web, API, desktop, DB, RPA)",
            "Good for BDD and acceptance testing",
            "Python-based - easy to extend",
            "Strong in enterprise and RPA use cases",
            "Free and open source (Apache 2.0)",
        ],
        cons=[
            "Tabular syntax can feel limiting for complex logic",
            "Slower execution (extra abstraction layer)",
            "IDE support less mature than code-based frameworks",
            "Debugging keyword failures can be frustrating",
            "Parallel execution requires third-party (Pabot)",
            "Web testing depends on SeleniumLibrary (inherits its issues)",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("9.5 Best Suited For")
    pdf._body(
        "- Teams with non-technical testers (keyword-driven approach)\n"
        "- Acceptance testing with business-readable test cases\n"
        "- Multi-domain testing (web + API + database in one suite)\n"
        "- Organizations using RPA alongside test automation\n"
        "- Python shops wanting an extensible test framework"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 10. NIGHTWATCH.JS
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("10", "Nightwatch.js", NW_COLOR)

    pdf._body(
        "Nightwatch.js is an integrated E2E testing framework for Node.js that uses the W3C "
        "WebDriver API and optionally the Chrome DevTools Protocol. It includes a built-in test "
        "runner, assertion library, and support for page objects. Nightwatch v3 added component "
        "testing for React, Vue, and Angular."
    )

    pdf._sub_title("10.1 Architecture & Key Features")
    pdf._body(
        "Nightwatch communicates with browsers via the WebDriver protocol (similar to Selenium) "
        "but bundles everything into one package with its own test runner.\n\n"
        "Key features:\n"
        "- Built-in test runner with parallel execution\n"
        "- Built-in assertion library (expect-style and assert-style)\n"
        "- Page Object Model support\n"
        "- CSS/XPath selectors + custom commands\n"
        "- BDD support with describe/it or exports syntax\n"
        "- Component testing (React, Vue, Angular)\n"
        "- Visual regression testing plugin\n"
        "- Native mobile testing via Appium\n"
        "- Integrated HTML reporter"
    )

    pdf._check_space(40)
    pdf._sub_title("10.2 Code Example")
    pdf._code_block("""
describe('Product Search', function() {
  it('should find products', function(browser) {
    browser
      .navigateTo('https://myapp.com')
      .setValue('[data-testid="search"]', 'laptop')
      .click('[data-testid="search-btn"]')
      .waitForElementVisible('.product-card')
      .expect.elements('.product-card').count.to.equal(5);
  });
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("10.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "All-in-one: test runner + assertions + reporter",
            "Simple, clean API for common operations",
            "Page Object Model built-in",
            "Component testing support",
            "Good BDD integration",
            "Free and open source",
        ],
        cons=[
            "JavaScript/TypeScript only",
            "Smaller community than Cypress/Playwright",
            "WebDriver-based (inherits flakiness issues)",
            "Slower execution than Playwright",
            "Documentation could be more comprehensive",
            "Fewer integrations than WebDriverIO",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("10.4 Best Suited For")
    pdf._body(
        "- Node.js teams wanting an all-in-one E2E solution\n"
        "- Projects needing component + E2E testing\n"
        "- Teams preferring a simpler API than WebDriverIO\n"
        "- Quick-start testing with minimal configuration"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 11. APPIUM
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("11", "Appium", AP_COLOR)

    pdf._body(
        "Appium is an open-source mobile automation framework that allows you to write tests for "
        "native, hybrid, and mobile web applications on iOS and Android. It extends the WebDriver "
        "protocol to mobile platforms, meaning if you know Selenium, you can use Appium with the "
        "same API. Appium 2.0 introduced a driver/plugin architecture for greater flexibility."
    )

    pdf._sub_title("11.1 Architecture")
    pdf._body(
        "Appium uses a client-server architecture:\n\n"
        "  Test Script --> Appium Server (Node.js) --> Platform Drivers --> Device/Simulator\n\n"
        "Platform Drivers:\n"
        "- XCUITest Driver: iOS automation via Apple's XCUITest\n"
        "- UiAutomator2 Driver: Android automation via Google's UiAutomator\n"
        "- Espresso Driver: Android automation via Google's Espresso\n"
        "- Mac2 Driver: macOS desktop automation\n"
        "- Windows Driver: Windows desktop automation\n\n"
        "Appium 2.0 uses a plugin architecture where drivers are installed separately, "
        "making the core lightweight and extensible."
    )

    pdf._sub_title("11.2 Key Features")
    for f in [
        "Cross-Platform Mobile: iOS, Android, Windows, macOS from one API",
        "WebDriver Protocol: Same API as Selenium (familiar for web testers)",
        "Native + Hybrid + Mobile Web: Test any mobile app type",
        "Multi-Language: Java, Python, C#, Ruby, JavaScript client libraries",
        "Real Devices + Simulators: Test on physical or virtual devices",
        "Appium Inspector: GUI tool for inspecting element hierarchies",
        "Cloud Integration: BrowserStack, Sauce Labs, AWS Device Farm",
        "Plugin Architecture (v2): Extensible with community drivers/plugins",
        "No App Modification: Tests run without modifying the app binary",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("11.3 Code Example")
    pdf._code_block("""
from appium import webdriver
from appium.options import UiAutomator2Options

options = UiAutomator2Options()
options.platform_name = 'Android'
options.device_name = 'emulator-5554'
options.app = '/path/to/app.apk'

driver = webdriver.Remote('http://127.0.0.1:4723', options=options)

search = driver.find_element('accessibility id', 'search-input')
search.send_keys('laptop')
driver.find_element('accessibility id', 'search-btn').click()

results = driver.find_elements('class name', 'product-card')
assert len(results) == 5

driver.quit()
""", "python")

    pdf._check_space(50)
    pdf._sub_title("11.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Cross-platform mobile (iOS + Android) from one API",
            "WebDriver-compatible (familiar API)",
            "Multi-language support",
            "Works with real devices and simulators",
            "No app modification required",
            "Cloud device farm integration",
            "Large community and ecosystem",
            "Plugin architecture (v2) for extensibility",
        ],
        cons=[
            "Slow test execution (startup + communication overhead)",
            "Complex setup (Node.js server + platform SDKs)",
            "Flaky on real devices (timing, connection issues)",
            "Limited for web-only testing (use Playwright instead)",
            "iOS testing requires macOS",
            "Debugging is challenging",
            "Learning curve for mobile-specific concepts",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("11.5 Best Suited For")
    pdf._body(
        "- Mobile app testing (native, hybrid, mobile web)\n"
        "- Teams with Selenium experience wanting to add mobile\n"
        "- Cross-platform mobile test automation (iOS + Android)\n"
        "- Integration with cloud device farms for scale"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 12. KATALON STUDIO
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("12", "Katalon Studio", KS_COLOR)

    pdf._body(
        "Katalon Studio is a comprehensive, low-code test automation platform that supports web, "
        "API, mobile, and desktop testing. Built on top of Selenium and Appium, it provides a "
        "visual IDE with record-and-playback, keyword-driven testing, and scripting capabilities "
        "(Groovy/Java). Katalon offers both free (Katalon Studio) and paid (Katalon Platform) tiers."
    )

    pdf._sub_title("12.1 Architecture & Key Features")
    pdf._body(
        "Katalon Studio is built on:\n"
        "- Selenium WebDriver for web testing\n"
        "- Appium for mobile testing\n"
        "- Groovy scripting language for test logic\n\n"
        "Key features:\n"
        "- Record & Playback: Record browser actions, generate test scripts\n"
        "- Dual Mode: Visual (keyword-driven) + Script (Groovy/Java) editing\n"
        "- Smart Wait: Auto-wait for elements before actions\n"
        "- Cross-browser: Chrome, Firefox, Edge, Safari, IE\n"
        "- API Testing: REST/SOAP/GraphQL testing built-in\n"
        "- Mobile Testing: iOS/Android via built-in Appium\n"
        "- Data-Driven: Excel, CSV, database-driven tests\n"
        "- CI/CD: Jenkins, Azure DevOps, GitLab CI plugins\n"
        "- Test Analytics: Katalon TestOps for reporting and insights\n"
        "- Self-healing: AI-powered locator self-healing"
    )

    pdf._check_space(40)
    pdf._sub_title("12.2 Code Example (Groovy)")
    pdf._code_block("""
import static com.kms.katalon.core.testobject.ObjectRepository.findTestObject
import com.kms.katalon.core.webui.keyword.WebUiBuiltInKeywords as WebUI

WebUI.openBrowser('')
WebUI.navigateToUrl('https://myapp.com')
WebUI.setText(findTestObject('search_input'), 'laptop')
WebUI.click(findTestObject('search_button'))
WebUI.verifyElementPresent(findTestObject('product_card'), 10)
WebUI.closeBrowser()
""", "groovy")

    pdf._check_space(50)
    pdf._sub_title("12.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Low barrier to entry (record & playback)",
            "Web + API + Mobile in one tool",
            "Dual mode: visual for beginners, script for advanced",
            "Built on Selenium/Appium (proven engines)",
            "Free tier available (Katalon Studio)",
            "Good CI/CD integration",
            "Self-healing locators",
        ],
        cons=[
            "Groovy scripting language (niche, not widely known)",
            "Slower execution than pure Selenium/Playwright",
            "Paid features gated behind Katalon Platform",
            "Large IDE application (resource-heavy)",
            "Vendor lock-in for advanced features",
            "Limited flexibility compared to code-first tools",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("12.4 Best Suited For")
    pdf._body(
        "- QA teams with mixed technical skill levels\n"
        "- Organizations wanting web + API + mobile in one tool\n"
        "- Teams transitioning from manual to automated testing\n"
        "- Small teams wanting quick automation without extensive coding"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 13. JEST + TESTING LIBRARY
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("13", "Jest + Testing Library", JT_COLOR)

    pdf._body(
        "Jest is Facebook's JavaScript testing framework, and Testing Library (by Kent C. Dodds) "
        "is a family of testing utilities that encourage testing from the user's perspective. "
        "Together, they are the dominant solution for React component and integration testing, "
        "though Testing Library also supports Vue, Angular, Svelte, and vanilla DOM testing."
    )

    pdf._sub_title("13.1 Architecture")
    pdf._body(
        "Jest + Testing Library operate at the component/unit level (not browser E2E):\n\n"
        "  Jest Test Runner --> jsdom (virtual DOM) --> Testing Library queries --> Component\n\n"
        "- Jest: Test runner, assertion library, mocking, code coverage, snapshot testing\n"
        "- Testing Library: DOM querying utilities that mirror how users interact with UI\n"
        "- jsdom: Simulated browser DOM in Node.js (no real browser needed)\n"
        "- React Testing Library: Most popular, renders React components in jsdom\n\n"
        "Note: This is NOT E2E testing. It tests components in isolation without a real browser. "
        "For E2E, use Playwright or Cypress alongside Jest + Testing Library."
    )

    pdf._sub_title("13.2 Key Features")
    for f in [
        "User-Centric Queries: getByRole, getByText, getByLabelText (how users find elements)",
        "Snapshot Testing: Capture and compare component output over time",
        "Mocking: Built-in function mocking, module mocking, timer mocking",
        "Code Coverage: Built-in Istanbul-based coverage reports",
        "Watch Mode: Re-run affected tests on file changes",
        "Parallel Execution: Worker-based parallel test execution",
        "Framework Support: React, Vue, Angular, Svelte, Preact, vanilla DOM",
        "User Events: @testing-library/user-event simulates real user interactions",
        "Async Utilities: waitFor, findBy queries for async operations",
        "Zero Config: Works out of the box with Create React App, Vite, Next.js",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("13.3 Code Example")
    pdf._code_block("""
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProductSearch from './ProductSearch';

test('user can search products', async () => {
  render(<ProductSearch />);

  // Query by role - how a user would find the element
  const input = screen.getByRole('searchbox');
  const button = screen.getByRole('button', { name: /search/i });

  await userEvent.type(input, 'laptop');
  await userEvent.click(button);

  // Wait for async results
  const cards = await screen.findAllByTestId('product-card');
  expect(cards).toHaveLength(5);
});
""", "jsx")

    pdf._check_space(50)
    pdf._sub_title("13.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Fastest feedback loop (no browser startup)",
            "User-centric testing philosophy",
            "Built-in mocking, coverage, snapshots",
            "Zero config with modern frameworks",
            "Encourages accessible, testable components",
            "Massive community (Jest: 44k stars)",
            "Works across React, Vue, Angular, Svelte",
        ],
        cons=[
            "Not E2E testing (no real browser, no navigation)",
            "jsdom doesn't implement all browser APIs",
            "Cannot test visual rendering or CSS",
            "Not suitable for cross-browser testing",
            "Snapshot tests can become noisy maintenance burden",
            "JavaScript/TypeScript only",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("13.5 Best Suited For")
    pdf._body(
        "- Component-level and unit testing (NOT E2E)\n"
        "- React/Vue/Angular/Svelte component testing\n"
        "- Testing business logic and user interactions\n"
        "- Fast feedback during development (TDD)\n"
        "- Complementing E2E tests (Playwright/Cypress) with component tests"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 14. K6
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("14", "k6 (Performance Testing)", K6_COLOR)

    pdf._body(
        "k6 is an open-source load and performance testing tool by Grafana Labs (formerly Load "
        "Impact). Written in Go with a JavaScript scripting API, k6 is designed for developers "
        "who want to write performance tests as code. It excels at HTTP API load testing but also "
        "supports browser-based testing via the k6-browser extension."
    )

    pdf._sub_title("14.1 Architecture")
    pdf._body(
        "k6 uses a unique architecture:\n\n"
        "  JavaScript Test Script --> Go Runtime (k6 engine) --> HTTP/WebSocket/gRPC\n\n"
        "- Test scripts are written in JavaScript (ES6+)\n"
        "- The Go runtime executes scripts with high efficiency (not Node.js)\n"
        "- Virtual Users (VUs) simulate concurrent users\n"
        "- Outputs metrics to console, JSON, InfluxDB, Prometheus, Grafana Cloud\n"
        "- k6-browser: Chromium-based browser testing for web performance\n"
        "- k6 Cloud: Distributed cloud execution for massive scale"
    )

    pdf._sub_title("14.2 Key Features")
    for f in [
        "Developer-Friendly: Write tests in JavaScript, version control, code review",
        "High Performance: Go runtime handles thousands of VUs per machine",
        "HTTP/2, WebSocket, gRPC: Multi-protocol load testing",
        "Thresholds: Define pass/fail criteria (e.g., p95 < 500ms)",
        "Scenarios: Model complex traffic patterns (ramp-up, spike, soak)",
        "Checks: Assertions on responses (like functional test assertions)",
        "Browser Testing: k6-browser for real browser performance metrics",
        "Grafana Integration: Native dashboards and alerting",
        "Extensions: Go-based extensions for custom protocols",
        "CI/CD Native: CLI-based, easy to integrate in pipelines",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("14.3 Code Example")
    pdf._code_block("""
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp up to 50 VUs
    { duration: '1m',  target: 50 },   // Hold at 50 VUs
    { duration: '10s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],     // <1% failure rate
  },
};

export default function () {
  const res = http.get('https://myapp.com/api/products');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body has products': (r) => r.json().length > 0,
  });
  sleep(1);
}
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("14.4 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Developer-friendly (JavaScript + code-as-tests)",
            "Extremely efficient (Go runtime, low resource usage)",
            "Rich metrics and Grafana integration",
            "Thresholds for automated pass/fail in CI",
            "Multi-protocol (HTTP, WebSocket, gRPC)",
            "Free and open source (AGPL v3)",
            "Cloud execution for distributed testing",
        ],
        cons=[
            "Not a functional E2E testing tool (primarily load testing)",
            "JavaScript only (not Python, Java, etc.)",
            "Browser testing is limited vs Playwright/Cypress",
            "No built-in HTML report (needs external tools)",
            "k6 Cloud is paid for advanced features",
            "Custom Go extensions needed for some protocols",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("14.5 Best Suited For")
    pdf._body(
        "- API load and performance testing\n"
        "- CI/CD pipeline performance gates\n"
        "- Stress, spike, and soak testing\n"
        "- Developer teams wanting tests-as-code for performance\n"
        "- Organizations using Grafana for monitoring"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 15. DETOX
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("15", "Detox (React Native)", DT_COLOR)

    pdf._body(
        "Detox is a gray-box E2E testing framework for React Native apps, developed by Wix. "
        "Unlike Appium (black-box), Detox hooks into the React Native runtime to synchronize "
        "with the app's internal state - waiting for animations, network calls, and JS execution "
        "to complete before each action. This dramatically reduces test flakiness."
    )

    pdf._sub_title("15.1 Architecture & Key Features")
    pdf._body(
        "Detox's gray-box approach:\n\n"
        "  Detox Client --> Native Driver --> App + Detox Server (inside app)\n\n"
        "- Synchronizes with React Native bridge, animations, and network\n"
        "- Runs on real iOS simulators and Android emulators\n"
        "- Uses EarlGrey (iOS) and Espresso (Android) under the hood\n"
        "- Built-in Jest integration as test runner\n"
        "- Automatic screenshots on test failure\n"
        "- Element matchers: by.id(), by.text(), by.label()\n"
        "- Device APIs: shake, rotate, set location, permissions\n"
        "- Parallel test execution across multiple simulators"
    )

    pdf._check_space(40)
    pdf._sub_title("15.2 Code Example")
    pdf._code_block("""
describe('Product Search', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should find products', async () => {
    await element(by.id('search-input')).typeText('laptop');
    await element(by.id('search-btn')).tap();

    await waitFor(element(by.id('product-card')))
      .toBeVisible()
      .withTimeout(5000);

    await expect(element(by.id('product-list'))).toBeVisible();
  });
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("15.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Gray-box testing - synchronizes with app state",
            "Dramatically less flaky than Appium for React Native",
            "Fast execution (native driver, no WebDriver overhead)",
            "Jest integration - familiar test runner",
            "Parallel execution across simulators",
            "Built specifically for React Native",
        ],
        cons=[
            "React Native only (not for native iOS/Android or web)",
            "iOS testing requires macOS",
            "Complex setup (native build tools required)",
            "Limited community compared to Appium",
            "JavaScript/TypeScript only",
            "No cloud device farm support (vs Appium)",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("15.4 Best Suited For")
    pdf._body(
        "- React Native app E2E testing\n"
        "- Teams frustrated with Appium's flakiness on React Native\n"
        "- CI/CD pipelines for React Native apps\n"
        "- Projects prioritizing test reliability over cross-platform breadth"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 16. GAUGE
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("16", "Gauge", GA_COLOR)

    pdf._body(
        "Gauge is an open-source test automation framework by ThoughtWorks (creators of Selenium). "
        "It focuses on writing tests in Markdown-like specifications that are both human-readable "
        "and executable. Gauge supports multiple languages (Java, C#, Python, JavaScript, Ruby, Go) "
        "and integrates with Selenium, Playwright, or any browser driver for web testing."
    )

    pdf._sub_title("16.1 Architecture & Key Features")
    pdf._body(
        "Gauge separates test specifications from implementation:\n\n"
        "  Specification (.spec file) --> Gauge Core --> Step Implementation --> Action\n\n"
        "- Markdown-based specs: readable by anyone\n"
        "- Step implementations: code behind each spec step\n"
        "- Data-driven testing via data tables in specs\n"
        "- Tags for test organization and filtering\n"
        "- Parallel execution with --parallel flag\n"
        "- Plugins: HTML report, XML report, Flash (live report)\n"
        "- IDE plugins: VS Code, IntelliJ IDEA\n"
        "- Multi-language: Java, C#, Python, JS, Ruby, Go\n"
        "- Screenshot on failure built-in"
    )

    pdf._check_space(40)
    pdf._sub_title("16.2 Code Example")
    pdf._code_block("""
# Product Search Specification

## User searches for products
* Navigate to "https://myapp.com"
* Type "laptop" in search box
* Click search button
* Verify "5" products are displayed
""", "markdown (.spec file)")

    pdf._code_block("""
# Step Implementation (Python)
from getgauge.python import step
from selenium import webdriver

driver = None

@step("Navigate to <url>")
def navigate(url):
    global driver
    driver = webdriver.Chrome()
    driver.get(url)

@step("Type <text> in search box")
def type_search(text):
    driver.find_element_by_css_selector('[data-testid="search"]').send_keys(text)

@step("Verify <count> products are displayed")
def verify_products(count):
    cards = driver.find_elements_by_css_selector('.product-card')
    assert len(cards) == int(count)
""", "python")

    pdf._check_space(50)
    pdf._sub_title("16.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Markdown specs - readable by business stakeholders",
            "Multi-language support (6+ languages)",
            "Clean separation of spec from implementation",
            "Built by ThoughtWorks (Selenium creators)",
            "Parallel execution built-in",
            "Free and open source",
        ],
        cons=[
            "Smaller community than Cucumber/BDD alternatives",
            "Browser testing requires separate library (Selenium/PW)",
            "Step matching can be fragile",
            "Less plugin ecosystem",
            "IDE support varies by language",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("16.4 Best Suited For")
    pdf._body(
        "- BDD/acceptance testing with business-readable specs\n"
        "- Multi-language teams (each can implement steps in their language)\n"
        "- Projects wanting cleaner spec format than Cucumber\n"
        "- ThoughtWorks / agile methodology shops"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 17. KARATE DSL
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("17", "Karate DSL", KA_COLOR)

    pdf._body(
        "Karate is an open-source framework that combines API testing, mocks, performance testing, "
        "and UI automation into a single unified framework. It uses a Gherkin-like BDD syntax but "
        "doesn't require step definitions - the DSL is directly executable. Karate is particularly "
        "powerful for API test automation and contract testing."
    )

    pdf._sub_title("17.1 Architecture & Key Features")
    pdf._body(
        "Karate runs on the JVM and integrates with JUnit:\n\n"
        "  .feature files (Gherkin DSL) --> Karate Engine (JVM) --> HTTP/Browser/Mock\n\n"
        "- No step definitions needed (DSL is self-contained)\n"
        "- API Testing: REST, SOAP, GraphQL with built-in assertions\n"
        "- JSON/XML: Native support for JSON path, XML path assertions\n"
        "- UI Testing: Built-in browser automation (Playwright-based in v1.3+)\n"
        "- Mocks: Built-in API mock server for contract testing\n"
        "- Performance: Gatling integration for load testing\n"
        "- Data-driven: Tables, dynamic data, scenario outlines\n"
        "- Parallel execution with JUnit 5\n"
        "- Comprehensive HTML reporting"
    )

    pdf._check_space(40)
    pdf._sub_title("17.2 Code Example")
    pdf._code_block("""
Feature: Product Search API

  Scenario: Search returns products
    Given url 'https://myapp.com/api/products'
    And param q = 'laptop'
    When method get
    Then status 200
    And match response.length == 5
    And match each response contains { name: '#string', price: '#number' }

  Scenario: UI search test
    Given driver 'https://myapp.com'
    When input('[data-testid="search"]', 'laptop')
    And click('[data-testid="search-btn"]')
    Then waitFor('.product-card')
    And match locateAll('.product-card').length == 5
""", "gherkin (.feature)")

    pdf._check_space(50)
    pdf._sub_title("17.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "API + UI + Performance in one framework",
            "No step definitions (DSL is self-contained)",
            "Excellent for API testing (best-in-class)",
            "Built-in mock server for contract testing",
            "Native JSON/XML assertions",
            "Parallel execution with JUnit",
            "Free and open source (MIT)",
        ],
        cons=[
            "JVM-only (Java/Kotlin ecosystem)",
            "UI testing is less mature than Playwright/Cypress",
            "Gherkin-like syntax has a learning curve",
            "Not ideal for complex UI-heavy test scenarios",
            "Community smaller than Selenium/Playwright",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("17.4 Best Suited For")
    pdf._body(
        "- API testing and contract testing\n"
        "- Teams wanting API + UI + performance in one tool\n"
        "- Java/JVM-based projects\n"
        "- Microservices testing with mock servers\n"
        "- Teams wanting BDD syntax without step definition boilerplate"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 18. CODECEPTJS
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("18", "CodeceptJS", CC_COLOR)

    pdf._body(
        "CodeceptJS is a modern E2E testing framework for Node.js that provides a unified API "
        "across multiple browser drivers (Playwright, Puppeteer, WebDriverIO, TestCafe, Appium). "
        "Its scenario-driven BDD syntax reads like plain English, making tests highly readable. "
        "You write tests once, then switch backends without changing test code."
    )

    pdf._sub_title("18.1 Architecture & Key Features")
    pdf._body(
        "CodeceptJS acts as an abstraction layer:\n\n"
        "  CodeceptJS Tests --> Helper (Playwright/Puppeteer/WDIO) --> Browser\n\n"
        "- Backend-agnostic: Switch between Playwright, Puppeteer, WebDriverIO, TestCafe\n"
        "- Scenario BDD syntax: I.click(), I.see(), I.fillField()\n"
        "- Page Objects and Page Fragments built-in\n"
        "- Interactive shell for debugging\n"
        "- Auto-retry and smart failure reporting\n"
        "- Data-driven testing with DataTable\n"
        "- Parallel execution with workers\n"
        "- AI-powered self-healing locators (heal plugin)"
    )

    pdf._check_space(40)
    pdf._sub_title("18.2 Code Example")
    pdf._code_block("""
Feature('Product Search');

Scenario('user can search products', ({ I }) => {
  I.amOnPage('https://myapp.com');
  I.fillField('[data-testid="search"]', 'laptop');
  I.click('[data-testid="search-btn"]');
  I.seeNumberOfElements('.product-card', 5);
  I.seeInCurrentUrl('search?q=laptop');
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("18.3 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Backend-agnostic (switch drivers without rewriting tests)",
            "Highly readable BDD syntax",
            "Interactive debugging shell",
            "Page Objects and auto-retry built-in",
            "Works with Playwright, Puppeteer, WDIO, TestCafe",
            "AI self-healing locators",
        ],
        cons=[
            "JavaScript/TypeScript only",
            "Extra abstraction layer (potential overhead)",
            "Smaller community than Playwright/Cypress",
            "Some driver-specific features not exposed",
            "Documentation can lag behind backends",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("18.4 Best Suited For")
    pdf._body(
        "- Teams wanting to switch between drivers without rewriting tests\n"
        "- BDD-style testing with readable scenario syntax\n"
        "- Teams evaluating multiple backends before committing\n"
        "- Projects needing both web and mobile testing (via Appium helper)"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 19. WATIR
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("19", "Watir", WA_COLOR)

    pdf._body(
        "Watir (Web Application Testing in Ruby) is a Ruby library for automating web browsers. "
        "One of the oldest browser automation tools (since 2001), it provides a clean, Ruby-like "
        "API built on top of Selenium WebDriver. Watir makes browser automation feel natural to "
        "Ruby developers with its object-oriented approach."
    )

    pdf._sub_title("19.1 Key Features & Code Example")
    pdf._body(
        "- Ruby-native API with readable syntax\n"
        "- Built on Selenium WebDriver\n"
        "- Automatic waits (Watir::Wait)\n"
        "- Element collections with Enumerable support\n"
        "- Support for Chrome, Firefox, Edge, Safari, IE\n"
        "- Page Object pattern support\n"
        "- Integration with RSpec and Cucumber"
    )

    pdf._code_block("""
require 'watir'

browser = Watir::Browser.new :chrome
browser.goto 'https://myapp.com'

browser.text_field(data_testid: 'search').set 'laptop'
browser.button(data_testid: 'search-btn').click

browser.divs(class: 'product-card').wait_until(size: 5)
puts browser.divs(class: 'product-card').size  # => 5

browser.close
""", "ruby")

    pdf._check_space(50)
    pdf._sub_title("19.2 Pros & Cons")
    pdf._pros_cons(
        pros=[
            "Beautiful Ruby-native API",
            "Built-in waits (less flakiness than raw Selenium)",
            "Good for Ruby/Rails teams",
            "Mature and stable",
        ],
        cons=[
            "Ruby only (niche language for testing)",
            "Built on Selenium (inherits its limitations)",
            "Smaller community than Selenium/Playwright",
            "No modern features (tracing, network mocking)",
            "Development pace has slowed",
        ],
    )

    pdf._check_space(30)
    pdf._sub_title("19.3 Best Suited For")
    pdf._body(
        "- Ruby/Rails teams wanting native-feeling browser automation\n"
        "- Projects already using RSpec or Cucumber in Ruby\n"
        "- Teams comfortable with Ruby ecosystem"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 20. PROTRACTOR (DEPRECATED)
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("20", "Protractor (Deprecated)", PR_COLOR)

    pdf._body(
        "Protractor was the official E2E testing framework for Angular applications, built on top "
        "of Selenium WebDriver. Developed by the Angular team at Google, it provided Angular-specific "
        "features like automatic waitForAngular() synchronization. Protractor was DEPRECATED in 2022 "
        "and reached end-of-life in August 2023. The Angular team now recommends Playwright or Cypress."
    )

    pdf._sub_title("20.1 Why It's Deprecated")
    pdf._body(
        "Protractor was deprecated for several reasons:\n"
        "- Built on Selenium 3 (never fully migrated to Selenium 4)\n"
        "- Angular-specific (not useful for other frameworks)\n"
        "- Modern alternatives (Playwright, Cypress) are superior in every way\n"
        "- waitForAngular() caused more problems than it solved in modern Angular\n"
        "- Community had already largely migrated away\n\n"
        "MIGRATION RECOMMENDATION:\n"
        "- Playwright: Best overall replacement (multi-browser, multi-language)\n"
        "- Cypress: Best for frontend-focused Angular teams\n"
        "- The Angular CLI now offers Cypress or Playwright as options via `ng e2e`"
    )

    pdf._check_space(40)
    pdf._sub_title("20.2 Legacy Code Example (For Reference)")
    pdf._code_block("""
// protractor.conf.js (DEPRECATED - DO NOT USE FOR NEW PROJECTS)
describe('Product Search', () => {
  it('should find products', () => {
    browser.get('https://myapp.com');
    element(by.css('[data-testid="search"]')).sendKeys('laptop');
    element(by.css('[data-testid="search-btn"]')).click();
    expect(element.all(by.css('.product-card')).count()).toBe(5);
  });
});
""", "javascript (DEPRECATED)")

    pdf._check_space(20)
    pdf._body(
        "If you have existing Protractor tests, migrate to Playwright or Cypress. "
        "Community migration guides are available at:\n"
        "- playwright.dev/docs/protractor\n"
        "- docs.cypress.io/guides/migrating-to-cypress/protractor"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 21. HEAD-TO-HEAD COMPARISON
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("21", "Head-to-Head Comparison")

    pdf._sub_title("21.1 Browser E2E Framework Comparison")
    pdf._table(
        ["Feature", "Playwright", "Selenium", "Cypress", "Puppeteer", "WDIO"],
        [
            ["Open Source",      "Yes",       "Yes",      "Yes",       "Yes",       "Yes"],
            ["Languages",        "JS/Py/Java/C#", "6+",   "JS/TS",    "JS/TS",     "JS/TS"],
            ["Chrome",           "Yes",       "Yes",      "Yes",       "Yes",       "Yes"],
            ["Firefox",          "Yes",       "Yes",      "Yes",       "Experimental","Yes"],
            ["Safari/WebKit",    "Yes",       "Yes",      "Experimental","No",      "Yes"],
            ["Auto-wait",        "Built-in",  "Manual",   "Built-in",  "Manual",    "Built-in"],
            ["Network Mock",     "Native",    "Proxy",    "Native",    "Native",    "Native"],
            ["Parallel",         "Built-in",  "Grid",     "Cloud($)",  "Manual",    "Built-in"],
            ["Mobile",           "Emulation", "Appium",   "No",        "No",        "Appium"],
            ["API Testing",      "Built-in",  "No",       "cy.request","No",        "No"],
            ["Component Test",   "Experimental","No",     "Built-in",  "No",        "Yes"],
            ["Debugging",        "Trace Viewer","Logs",   "Time-Travel","CDP",      "Logs"],
        ],
        [30, 30, 28, 28, 28, 30],
    )

    pdf._sub_title("21.2 Specialized Framework Comparison")
    pdf._table(
        ["Framework", "Type", "Language", "Best For"],
        [
            ["Tosca",        "Enterprise/No-code", "Scriptless",  "SAP, enterprise"],
            ["Katalon",      "Low-code",           "Groovy/Java", "Mixed-skill QA teams"],
            ["Robot Framework","Keyword-driven",    "Python-based","BDD + multi-domain"],
            ["Appium",       "Mobile",             "Multi-lang",  "Native/hybrid mobile"],
            ["Detox",        "Mobile",             "JS/TS",       "React Native"],
            ["k6",           "Performance",        "JavaScript",  "Load/stress testing"],
            ["Jest + RTL",   "Component/Unit",     "JS/TS",       "React component tests"],
            ["Karate",       "API + UI",           "JVM",         "API testing + mocks"],
            ["Gauge",        "BDD/Acceptance",     "Multi-lang",  "Markdown-based specs"],
            ["CodeceptJS",   "E2E (abstraction)",  "JS/TS",       "Backend-agnostic E2E"],
            ["Nightwatch",   "E2E",                "JS/TS",       "Simple all-in-one E2E"],
        ],
        [35, 38, 32, 69],
    )

    pdf.add_page()
    pdf._bg()
    pdf._sub_title("21.3 Performance Benchmarks (Indicative)")
    pdf._dim_body(
        "Note: Benchmarks vary by machine and application. These are representative values."
    )
    pdf._table(
        ["Metric", "Playwright", "Selenium", "Cypress", "Puppeteer"],
        [
            ["Cold start time",        "~2s",      "~3-5s",    "~4-6s",   "~1.5s"],
            ["Simple navigation test",  "~200ms",   "~500ms",   "~350ms",  "~180ms"],
            ["Form fill + submit",      "~400ms",   "~1000ms",  "~600ms",  "~350ms"],
            ["10 parallel tests",       "~8s",      "~25s",     "~15s",    "~10s"],
            ["Network mock overhead",   "~5ms",     "~50ms",    "~10ms",   "~5ms"],
            ["Memory per browser",      "~150MB",   "~200MB",   "~300MB",  "~140MB"],
        ],
        [44, 32, 32, 32, 32],
    )

    pdf._sub_title("21.4 Community & Ecosystem (2026)")
    pdf._table(
        ["Metric", "Playwright", "Selenium", "Cypress", "Puppeteer"],
        [
            ["GitHub Stars",       "~70k",     "~31k",    "~47k",    "~89k"],
            ["NPM Weekly DL",     "~8M",      "~3M",     "~5M",     "~4M"],
            ["Stack Overflow Q's", "~18k",     "~150k+",  "~35k",    "~25k"],
            ["First Release",     "2020",      "2004",    "2017",    "2017"],
            ["Plugin Ecosystem",  "Growing",   "Massive", "700+",    "Large"],
        ],
        [40, 32, 32, 32, 32],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 22. SETUP & QUICK START
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("22", "Setup & Quick Start Guide")

    pdf._sub_title("22.1 Playwright Setup")
    pdf._code_block("""
# Node.js
npm init -y && npm install -D @playwright/test
npx playwright install
npx playwright test

# Python
pip install playwright pytest-playwright
playwright install chromium
pytest
""", "bash")

    pdf._sub_title("22.2 Selenium Setup")
    pdf._code_block("""
# Python
pip install selenium pytest
# Selenium Manager auto-downloads drivers
pytest

# Java (Maven) - add to pom.xml:
# org.seleniumhq.selenium:selenium-java:4.18.0
""", "bash")

    pdf._sub_title("22.3 Cypress Setup")
    pdf._code_block("""
npm init -y && npm install -D cypress
npx cypress open      # Interactive mode
npx cypress run       # Headless mode
""", "bash")

    pdf._sub_title("22.4 Puppeteer Setup")
    pdf._code_block("""
npm init -y && npm install puppeteer
# Chromium downloaded automatically
node test.js
""", "bash")

    pdf._sub_title("22.5 WebDriverIO Setup")
    pdf._code_block("""
npm init wdio@latest   # Interactive setup wizard
npx wdio run wdio.conf.js
""", "bash")

    pdf._check_space(40)
    pdf._sub_title("22.6 TestCafe Setup")
    pdf._code_block("""
npm install -D testcafe
npx testcafe chrome tests/
""", "bash")

    pdf._sub_title("22.7 Robot Framework Setup")
    pdf._code_block("""
pip install robotframework robotframework-seleniumlibrary
robot tests/
""", "bash")

    pdf._sub_title("22.8 k6 Setup")
    pdf._code_block("""
# macOS
brew install k6

# Windows
choco install k6

# Run
k6 run script.js
""", "bash")

    pdf._sub_title("22.9 Appium Setup")
    pdf._code_block("""
npm install -g appium
appium driver install uiautomator2   # Android
appium driver install xcuitest       # iOS
appium                               # Start server
""", "bash")

    # ═══════════════════════════════════════════════════════════════════
    # 23. CI/CD INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("23", "CI/CD Integration Patterns")

    pdf._sub_title("23.1 GitHub Actions - Playwright")
    pdf._code_block("""
name: E2E Tests (Playwright)
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: report, path: playwright-report/ }
""", "yaml")

    pdf._sub_title("23.2 GitHub Actions - Cypress")
    pdf._code_block("""
name: E2E Tests (Cypress)
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cypress-io/github-action@v6
        with:
          browser: chrome
          start: npm start
          wait-on: http://localhost:3000
""", "yaml")

    pdf._sub_title("23.3 GitHub Actions - k6 Performance")
    pdf._code_block("""
name: Performance Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: grafana/k6-action@v0.3.1
        with:
          filename: tests/load-test.js
""", "yaml")

    pdf._check_space(40)
    pdf._sub_title("23.4 Docker-Based Execution")
    pdf._code_block("""
# Playwright
FROM mcr.microsoft.com/playwright:v1.42.0-jammy
WORKDIR /app
COPY . .
RUN npm ci
CMD ["npx", "playwright", "test"]

# Cypress
FROM cypress/included:13.6.0
WORKDIR /app
COPY . .
CMD ["npx", "cypress", "run"]
""", "dockerfile")

    # ═══════════════════════════════════════════════════════════════════
    # 24. DECISION FRAMEWORK
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("24", "Decision Framework")

    pdf._sub_title("24.1 Quick Decision Tree")
    pdf._body("Answer these questions in order:\n")

    decisions = [
        ("What type of testing do you need?",
         "Performance -> k6  |  Mobile Native -> Appium/Detox  |  API-only -> Karate  |  Web E2E -> Continue"),
        ("Do you need SAP, Desktop, or Mainframe testing?",
         "YES -> Tosca  |  NO -> Continue"),
        ("Is your team primarily non-technical QA?",
         "YES -> Tosca or Katalon  |  NO -> Continue"),
        ("Is your app React Native?",
         "YES -> Detox  |  NO -> Continue"),
        ("Do you need IE11 support?",
         "YES -> Selenium  |  NO -> Continue"),
        ("Do you need true Safari/WebKit testing?",
         "YES -> Playwright  |  NO -> Continue"),
        ("Is DX and time-travel debugging your top priority?",
         "YES -> Cypress  |  NO -> Continue"),
        ("Do you need Python/Java/C# support?",
         "YES -> Playwright or Selenium  |  NO -> Continue"),
        ("Do you need web + mobile in one framework?",
         "YES -> WebDriverIO  |  NO -> Continue"),
        ("Are you starting a new project from scratch?",
         "YES -> Playwright (recommended)  |  NO -> Evaluate migration cost"),
    ]

    for q, a in decisions:
        pdf._check_space(16)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*TEXT_WHITE)
        pdf.cell(0, 6, f"Q: {q}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*ACCENT_LIGHT)
        pdf.cell(0, 6, f"   {a}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf._check_space(40)
    pdf._sub_title("24.2 Recommendation Summary")
    pdf._table(
        ["Scenario", "Recommended", "Runner-up"],
        [
            ["New project, any stack",       "Playwright",       "Cypress"],
            ["Frontend-heavy React/Vue",     "Cypress",          "Playwright"],
            ["Enterprise, SAP, multi-tech",  "Tosca",            "Katalon"],
            ["Python/Java backend team",     "Playwright",       "Selenium"],
            ["Legacy browser support",       "Selenium",         "Tosca"],
            ["Non-technical QA team",        "Katalon",          "Tosca"],
            ["Mobile native apps",           "Appium",           "Detox (RN)"],
            ["React Native specifically",    "Detox",            "Appium"],
            ["API + contract testing",       "Karate",           "Playwright"],
            ["Performance/load testing",     "k6",               "Artillery"],
            ["Component testing",            "Jest + RTL",       "Vitest"],
            ["BDD acceptance testing",       "Gauge",            "Robot Framework"],
            ["Web + Mobile one framework",   "WebDriverIO",      "Appium"],
            ["Maximum browser coverage",     "Playwright",       "Selenium"],
            ["Budget-conscious startup",     "Playwright",       "Cypress"],
        ],
        [52, 40, 82],
    )

    pdf._check_space(40)
    pdf._sub_title("24.3 Migration Guide")
    pdf._body(
        "Common migration paths:\n\n"
        "Protractor -> Playwright: Official migration guide at playwright.dev. Budget 2-3 weeks.\n\n"
        "Selenium -> Playwright: Similar API structure. Remove explicit waits, use auto-wait. "
        "Budget 2-4 weeks for a medium test suite.\n\n"
        "Selenium -> Cypress: Different paradigm (chain-based). Multi-tab tests need redesign. "
        "Budget 4-6 weeks.\n\n"
        "Cypress -> Playwright: Both use async patterns. Network mocking translates well. "
        "Budget 2-3 weeks.\n\n"
        "Puppeteer -> Playwright: Nearly 1:1 API. Add multi-browser support. Budget 1-2 weeks.\n\n"
        "Any -> Tosca: Complete paradigm shift to model-based. Budget 2-3 months with training."
    )

    # ═══════════════════════════════════════════════════════════════════
    # 25. GLOSSARY & RESOURCES
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    pdf._section_title("25", "Glossary & Resources")

    pdf._sub_title("25.1 Glossary")
    terms = [
        ("E2E Testing", "Testing the complete flow from the user's perspective"),
        ("CDP", "Chrome DevTools Protocol - low-level API to control Chromium"),
        ("W3C WebDriver", "Official web standard for browser automation"),
        ("SPA", "Single Page Application - client-side rendered app"),
        ("SSR", "Server-Side Rendering - HTML generated on server"),
        ("Flaky Test", "Test that passes and fails intermittently"),
        ("Auto-wait", "Framework automatically waits for elements to be ready"),
        ("Headless", "Running browser without visible UI (for CI/CD)"),
        ("Page Object Model", "Design pattern encapsulating page interactions"),
        ("Browser Context", "Isolated browser session with own cookies/storage"),
        ("Visual Regression", "Detecting UI changes via screenshot comparison"),
        ("Gray-box Testing", "Testing with some knowledge of app internals (e.g., Detox)"),
        ("Load Testing", "Testing system behavior under expected load (k6)"),
        ("Stress Testing", "Testing system limits beyond normal capacity"),
        ("Contract Testing", "Verifying API producer/consumer agreements"),
        ("BDD", "Behavior-Driven Development - spec-first testing approach"),
        ("Virtual User (VU)", "Simulated concurrent user in load testing"),
    ]
    for term, defn in terms:
        pdf._check_space(12)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ACCENT_LIGHT)
        pdf.cell(0, 6, term, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_WHITE)
        pdf.cell(0, 5, f"  {defn}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf._check_space(50)
    pdf._sub_title("25.2 Official Resources")
    resources = [
        ("Playwright", "playwright.dev"),
        ("Selenium", "selenium.dev/documentation"),
        ("Cypress", "docs.cypress.io"),
        ("Tosca", "documentation.tricentis.com"),
        ("Puppeteer", "pptr.dev"),
        ("WebDriverIO", "webdriver.io"),
        ("TestCafe", "testcafe.io/documentation"),
        ("Robot Framework", "robotframework.org"),
        ("Nightwatch.js", "nightwatchjs.org"),
        ("Appium", "appium.io/docs"),
        ("Katalon", "docs.katalon.com"),
        ("Jest", "jestjs.io"),
        ("Testing Library", "testing-library.com"),
        ("k6", "k6.io/docs"),
        ("Detox", "wix.github.io/Detox"),
        ("Gauge", "docs.gauge.org"),
        ("Karate", "karatelabs.github.io/karate"),
        ("CodeceptJS", "codecept.io"),
    ]
    for name, url in resources:
        pdf._check_space(8)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*TEXT_WHITE)
        pdf.cell(40, 6, name)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*ACCENT_LIGHT)
        pdf.cell(0, 6, url, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════════════════════
    output_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(output_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, "testing-frameworks-guide.pdf")

    pdf.output(output_path)
    print(f"\nPDF generated: {output_path}")
    print(f"Pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    generate_doc()
