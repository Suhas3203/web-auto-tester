#!/usr/bin/env python3
"""
Generates comprehensive PDF documents covering ALL major testing frameworks.
Outputs both DARK and LIGHT themed PDFs.

Usage:
    python generate_testing_frameworks_doc.py
    python generate_testing_frameworks_doc.py --theme dark
    python generate_testing_frameworks_doc.py --theme light
    python generate_testing_frameworks_doc.py --theme both   (default)
"""

from fpdf import FPDF
import os
import sys

# ─── Theme definitions ────────────────────────────────────────────────────────

DARK_THEME = {
    "name": "dark",
    "bg":           (15, 17, 23),
    "surface":      (26, 29, 39),
    "surface2":     (36, 40, 54),
    "border":       (46, 51, 72),
    "text":         (225, 228, 237),
    "text_dim":     (139, 143, 163),
    "accent":       (99, 102, 241),
    "accent_light": (129, 140, 248),
    "pass":         (34, 197, 94),
    "fail":         (239, 68, 68),
    "warn":         (245, 158, 11),
    "code_bg":      (36, 40, 54),
    "code_text":    (200, 210, 230),
    "code_border":  (46, 51, 72),
    "table_hdr_text": (255, 255, 255),
    "table_row_even": (26, 29, 39),
    "table_row_odd":  (36, 40, 54),
    "pros_header_text": (15, 17, 23),
    "cons_header_text": (255, 255, 255),
    "cover_grad_start": (30, 27, 75),
    "cover_grad_end":   (99, 102, 241),
    "header_bg":    (26, 29, 39),
}

LIGHT_THEME = {
    "name": "light",
    "bg":           (255, 255, 255),
    "surface":      (245, 246, 250),
    "surface2":     (235, 237, 242),
    "border":       (210, 214, 224),
    "text":         (30, 32, 40),
    "text_dim":     (100, 105, 120),
    "accent":       (79, 82, 212),
    "accent_light": (79, 82, 212),
    "pass":         (22, 160, 70),
    "fail":         (210, 50, 50),
    "warn":         (200, 130, 0),
    "code_bg":      (243, 244, 248),
    "code_text":    (40, 44, 60),
    "code_border":  (210, 214, 224),
    "table_hdr_text": (255, 255, 255),
    "table_row_even": (250, 251, 254),
    "table_row_odd":  (240, 241, 246),
    "pros_header_text": (255, 255, 255),
    "cons_header_text": (255, 255, 255),
    "cover_grad_start": (200, 200, 240),
    "cover_grad_end":   (79, 82, 212),
    "header_bg":    (245, 246, 250),
}

# Framework brand colors (same for both themes)
FW_COLORS = {
    "playwright":  (45, 206, 137),
    "selenium":    (67, 176, 42),
    "cypress":     (36, 193, 224),
    "tosca":       (0, 120, 215),
    "puppeteer":   (0, 150, 136),
    "webdriverio": (234, 89, 12),
    "testcafe":    (54, 179, 126),
    "robot":       (0, 160, 0),
    "nightwatch":  (236, 100, 75),
    "appium":      (128, 0, 128),
    "katalon":     (23, 162, 184),
    "jest":        (198, 72, 56),
    "k6":          (126, 58, 242),
    "detox":       (120, 120, 120),
    "gauge":       (244, 168, 54),
    "karate":      (200, 50, 50),
    "codeceptjs":  (40, 116, 166),
    "watir":       (0, 128, 128),
    "protractor":  (211, 47, 47),
}


class TestingFrameworkDoc(FPDF):
    """PDF document with theme-aware rendering."""

    def __init__(self, theme: dict):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.t = theme
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 18, 18)

    # ── Header / Footer ─────────────────────────────────────────────────

    def header(self):
        if self.page_no() <= 2:  # Skip cover + TOC
            return
        self.set_fill_color(*self.t["header_bg"])
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.t["text_dim"])
        self.set_xy(18, 3)
        self.cell(0, 6, "Testing Frameworks - Comprehensive Guide", align="L")
        self.set_xy(18, 3)
        self.cell(174, 6, f"Page {self.page_no()}", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.t["text_dim"])
        self.cell(0, 10,
                  "Go Digital Technology Consulting LLP  |  March 2026  |  For internal use",
                  align="C")

    # ── Helpers ──────────────────────────────────────────────────────────

    def _bg(self):
        """Paint full-page background."""
        self.set_fill_color(*self.t["bg"])
        self.rect(0, 0, 210, 297, "F")

    def _new_page(self):
        """Add a page and paint background."""
        self.add_page()
        self._bg()

    def _section_title(self, num, title, color=None):
        if color is None:
            color = self.t["accent"]
        self.set_fill_color(*color)
        self.rect(18, self.get_y(), 174, 1.5, "F")
        self.ln(5)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*self.t["text"])
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def _sub_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.t["accent_light"])
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def _sub2_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.t["accent_light"])
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def _body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.t["text"])
        self.multi_cell(174, 5.5, text)
        self.ln(3)

    def _dim_body(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.t["text_dim"])
        self.multi_cell(174, 5, text)
        self.ln(2)

    def _code_block(self, code, lang=""):
        lines = code.strip().split("\n")
        block_h = len(lines) * 4.5 + 6
        lang_h = 5 if lang else 0
        total_h = block_h + lang_h

        # Check if we need a new page
        if self.get_y() + total_h > 275:
            self._new_page()

        y = self.get_y()

        # Language label
        if lang:
            self.set_fill_color(*self.t["code_bg"])
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*self.t["text_dim"])
            self.cell(174, 5, f"  {lang}", new_x="LMARGIN", new_y="NEXT", fill=True)
            y = self.get_y()

        # Code background with border
        self.set_fill_color(*self.t["code_bg"])
        self.set_draw_color(*self.t["code_border"])
        self.rect(18, y, 174, block_h, "DF")

        # Code text
        self.set_font("Courier", "", 8.5)
        self.set_text_color(*self.t["code_text"])
        self.set_xy(21, y + 3)
        for line in lines:
            self.cell(168, 4.5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(21)
        self.ln(4)

    def _bullet(self, text, indent=18):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.t["text"])
        self.set_x(indent)
        self.cell(5, 5.5, "-")
        self.multi_cell(174 - (indent - 18) - 5, 5.5, text)
        self.ln(1)

    def _pros_cons(self, pros, cons):
        col_w = 85
        y_start = self.get_y()

        if y_start + 10 + max(len(pros), len(cons)) * 6 > 275:
            self._new_page()
            y_start = self.get_y()

        # Pros header
        self.set_fill_color(*self.t["pass"])
        self.rect(18, y_start, col_w, 7, "F")
        self.set_xy(18, y_start)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.t["pros_header_text"])
        self.cell(col_w, 7, "  PROS", align="L")

        # Cons header
        self.set_fill_color(*self.t["fail"])
        self.rect(18 + col_w + 4, y_start, col_w, 7, "F")
        self.set_xy(18 + col_w + 4, y_start)
        self.set_text_color(*self.t["cons_header_text"])
        self.cell(col_w, 7, "  CONS", align="L")

        y = y_start + 9
        max_items = max(len(pros), len(cons))
        self.set_font("Helvetica", "", 9)

        for i in range(max_items):
            if y > 275:
                self._new_page()
                y = self.get_y()

            if i < len(pros):
                self.set_text_color(*self.t["pass"])
                self.set_xy(18, y)
                self.cell(3, 5, "+")
                self.set_text_color(*self.t["text"])
                self.cell(col_w - 3, 5, f" {pros[i]}")

            if i < len(cons):
                self.set_text_color(*self.t["fail"])
                self.set_xy(18 + col_w + 4, y)
                self.cell(3, 5, "-")
                self.set_text_color(*self.t["text"])
                self.cell(col_w - 3, 5, f" {cons[i]}")

            y += 6

        self.set_y(y + 4)

    def _table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [174 // len(headers)] * len(headers)

        needed = 8 + len(rows) * 7
        if self.get_y() + needed > 275:
            self._new_page()

        # Header row
        self.set_fill_color(*self.t["accent"])
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.t["table_hdr_text"])
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
                self._new_page()

            bg = self.t["table_row_even"] if ri % 2 == 0 else self.t["table_row_odd"]
            self.set_fill_color(*bg)
            x = 18
            for i, cell_text in enumerate(row):
                self.set_xy(x, self.get_y())
                self.set_text_color(*self.t["text"])
                self.cell(col_widths[i], 7, f" {cell_text}", fill=True)
                x += col_widths[i]
            self.ln(7)

        self.ln(4)

    def _check_space(self, needed=40):
        if self.get_y() + needed > 270:
            self._new_page()


# ═══════════════════════════════════════════════════════════════════════════════
# Content builder — shared across themes
# ═══════════════════════════════════════════════════════════════════════════════

def build_content(pdf: TestingFrameworkDoc):
    """Build all PDF content. Called once per theme."""
    t = pdf.t

    # ── COVER PAGE ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf._bg()

    # Gradient accent bar
    gs = t["cover_grad_start"]
    ge = t["cover_grad_end"]
    for i in range(80):
        r = int(gs[0] + (ge[0] - gs[0]) * i / 80)
        g = int(gs[1] + (ge[1] - gs[1]) * i / 80)
        b = int(gs[2] + (ge[2] - gs[2]) * i / 80)
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 60 + i * 0.8, 210, 0.8, "F")

    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*t["text"])
    pdf.set_xy(18, 72)
    pdf.cell(174, 18, "Testing Frameworks", align="L")
    pdf.set_xy(18, 90)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(*t["accent_light"])
    pdf.cell(174, 10, "Comprehensive Guide & Comparison", align="L")

    pdf.set_xy(18, 108)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*t["text_dim"])
    pdf.cell(174, 6, "Playwright | Selenium | Cypress | Tosca | Puppeteer | WebDriverIO", align="L")
    pdf.set_xy(18, 115)
    pdf.cell(174, 6, "TestCafe | Robot Framework | Nightwatch.js | Appium | Katalon Studio", align="L")
    pdf.set_xy(18, 122)
    pdf.cell(174, 6, "Jest + Testing Library | k6 | Detox | Gauge | Karate | CodeceptJS | Watir", align="L")

    pdf.set_xy(18, 142)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*t["text"])
    pdf.multi_cell(174, 6.5,
        "A complete reference covering 19+ testing and automation frameworks. "
        "Includes architecture, setup, code examples, pros & cons, performance "
        "benchmarks, and a decision framework for choosing the right tool.")

    # Tags
    tags = ["Playwright", "Selenium", "Cypress", "Tosca", "Puppeteer", "WebDriverIO",
            "TestCafe", "Robot Framework", "Appium", "k6", "Jest", "E2E Testing",
            "Python", "JavaScript", "TypeScript", "Java", "CI/CD", "Performance"]
    pdf.set_xy(18, 178)
    x = 18
    for tag in tags:
        w = pdf.get_string_width(tag) + 12
        if x + w > 192:
            x = 18
            pdf.ln(9)
            pdf.set_x(18)
        pdf.set_fill_color(*t["accent"])
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(x)
        pdf.cell(w, 7, tag, fill=True, align="C")
        x += w + 4

    pdf.set_xy(18, 260)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*t["text_dim"])
    mode = "Dark" if t["name"] == "dark" else "Light"
    pdf.cell(174, 6, f"Version 2.0.0  |  March 2026  |  {mode} Edition  |  Go Digital Technology Consulting LLP", align="L")

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────
    pdf._new_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*t["text"])
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
        pdf.set_text_color(*t["text"])
        pdf.cell(12, 7, num)
        pdf.cell(150, 7, title)
        pdf.ln(7)
        pdf.set_draw_color(*t["border"])
        y = pdf.get_y() - 3
        pdf.line(30, y, 192, y)
        if pdf.get_y() > 270:
            pdf._new_page()

    # ── 1. OVERVIEW ───────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("1", "Overview & Testing Landscape")
    pdf._body(
        "End-to-end (E2E) testing validates that an application works correctly from the user's "
        "perspective by automating browser interactions. The testing framework landscape has evolved "
        "significantly - from Selenium's dominance since 2004 to modern alternatives like Playwright "
        "and Cypress that address long-standing pain points around flakiness, speed, and developer "
        "experience. Today, there are 19+ major frameworks covering browser E2E, mobile, API, "
        "performance, and component testing.")

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
        [34, 80, 60])

    pdf._sub_title("1.2 Testing Pyramid Context")
    pdf._body(
        "E2E tests sit at the top of the testing pyramid:\n"
        "- Unit tests: 70-80% (fast, isolated) - Jest, Vitest, pytest\n"
        "- Integration tests: 15-20% (API/service level) - Karate, Supertest\n"
        "- E2E tests: 5-10% (critical user journeys) - Playwright, Cypress, Selenium\n"
        "- Performance tests: As needed - k6, Artillery\n"
        "- Mobile tests: As needed - Appium, Detox")

    pdf._sub_title("1.3 Key Selection Criteria")
    pdf._body(
        "When evaluating a testing framework, consider:\n\n"
        "- Browser Coverage: Which browsers must you support?\n"
        "- Language Ecosystem: What does your team already know?\n"
        "- Speed & Parallelism: How fast can tests run in CI?\n"
        "- Debugging Experience: How easy is it to diagnose failures?\n"
        "- Flakiness: How reliable are tests without manual waits?\n"
        "- Mobile Testing: Do you need native mobile support?\n"
        "- Cost: Open-source vs. licensed?\n"
        "- Community & Ecosystem: Plugins, docs, hiring pool?")

    # ── 2. PLAYWRIGHT ─────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("2", "Playwright", FW_COLORS["playwright"])
    pdf._body(
        "Playwright is an open-source browser automation framework by Microsoft, released in 2020. "
        "Built by the same team behind Puppeteer, it controls Chromium, Firefox, and WebKit through "
        "a single API using direct browser protocol connections.")

    pdf._sub_title("2.1 Architecture")
    pdf._body(
        "Playwright communicates via WebSocket to a Playwright Server that speaks each browser's "
        "native protocol:\n\n"
        "  Test Code --> Playwright Server --> CDP (Chromium)\n"
        "                                 --> Firefox Protocol\n"
        "                                 --> WebKit Protocol\n\n"
        "- No HTTP overhead (unlike Selenium)\n"
        "- Browser contexts share a single browser process\n"
        "- Each context gets its own cookies, storage, and permissions")

    pdf._sub_title("2.2 Key Features")
    for f in [
        "Auto-wait: Every action auto-waits for elements to be actionable",
        "Multi-browser: Chromium, Firefox, WebKit from one API",
        "Browser Contexts: Lightweight isolated sessions",
        "Network Interception: Native route() API for mocking/stubbing",
        "Tracing: Built-in trace viewer with DOM snapshots",
        "Codegen: Record actions and generate test code",
        "API Testing: Built-in request context for REST APIs",
        "Visual Comparisons: Pixel-level screenshot diffing",
        "Parallelism: Worker-based sharding out of the box",
        "Mobile Emulation: Device profiles for viewport, touch, geolocation",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("2.3 Language Support")
    pdf._table(
        ["Language", "Package", "Test Runner", "Maturity"],
        [
            ["JavaScript/TS", "@playwright/test", "Built-in", "Primary"],
            ["Python", "playwright (pip)", "pytest-playwright", "Official"],
            ["Java", "com.microsoft.playwright", "JUnit / TestNG", "Official"],
            ["C# / .NET", "Microsoft.Playwright", "NUnit / MSTest", "Official"],
        ],
        [32, 45, 52, 45])

    pdf._check_space(40)
    pdf._sub_title("2.4 Code Examples")
    pdf._sub2_title("TypeScript")
    pdf._code_block("""
import { test, expect } from '@playwright/test';

test('user can search products', async ({ page }) => {
  await page.goto('https://myapp.com');
  await page.fill('[data-testid="search"]', 'laptop');
  await page.click('[data-testid="search-btn"]');
  await expect(page.locator('.product-card')).toHaveCount(5);
});
""", "typescript")

    pdf._sub2_title("Python")
    pdf._code_block("""
from playwright.sync_api import Page, expect

def test_search_products(page: Page):
    page.goto("https://myapp.com")
    page.fill('[data-testid="search"]', 'laptop')
    page.click('[data-testid="search-btn"]')
    expect(page.locator(".product-card")).to_have_count(5)
""", "python")

    pdf._check_space(50)
    pdf._sub_title("2.5 Pros & Cons")
    pdf._pros_cons(
        pros=["Fastest execution - direct browser protocol", "True cross-browser (Chromium, Firefox, WebKit)",
              "Auto-wait eliminates most flakiness", "Built-in trace viewer debugging",
              "4 official languages", "Parallel execution out of the box", "Free and open source"],
        cons=["Newer (2020) - smaller community than Selenium", "No IE11 support",
              "Browser binaries ~400MB download", "No native mobile app testing"])

    pdf._check_space(20)
    pdf._sub_title("2.6 Best Suited For")
    pdf._body("- New projects from scratch\n- True cross-browser testing including Safari/WebKit\n"
              "- Python, Java, or C# shops\n- CI/CD pipelines needing fast, parallel, reliable tests")

    # ── 3. SELENIUM ───────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("3", "Selenium WebDriver", FW_COLORS["selenium"])
    pdf._body(
        "Selenium is the oldest and most widely adopted browser automation framework (2004). "
        "Selenium WebDriver became a W3C standard in 2018. Selenium 4 (2021) added relative "
        "locators, CDP access, and improved Grid for distributed testing.")

    pdf._sub_title("3.1 Architecture")
    pdf._body(
        "  Test Code --> Language Binding --> HTTP/JSON --> Browser Driver --> Browser\n\n"
        "Components: WebDriver API, Browser Drivers (chromedriver, geckodriver), Selenium Grid, "
        "Selenium IDE, Selenium Manager (auto-downloads drivers since 4.6+).")

    pdf._sub_title("3.2 Key Features")
    for f in [
        "W3C Standard: Only framework backed by official web standard",
        "6+ Languages: Java, Python, C#, Ruby, JavaScript, Kotlin",
        "Selenium Grid: Distributed execution across machines",
        "Selenium IDE: Record-and-playback browser extension",
        "Selenium Manager: Auto-manages driver binaries",
        "Cloud Grids: BrowserStack, Sauce Labs, LambdaTest",
        "Legacy Support: IE11, older Edge",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("3.3 Code Example")
    pdf._code_block("""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_search():
    driver = webdriver.Chrome()
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
    driver.quit()
""", "python")

    pdf._check_space(50)
    pdf._sub_title("3.4 Pros & Cons")
    pdf._pros_cons(
        pros=["W3C standard - future-proof", "Widest language support", "Largest community",
              "Selenium Grid for scale", "IE11 and legacy support", "20 years battle-tested"],
        cons=["No auto-wait (explicit waits needed)", "Slower (HTTP protocol overhead)",
              "Flakiness from timing issues", "No network interception", "Verbose code"])

    pdf._check_space(20)
    pdf._sub_title("3.5 Best Suited For")
    pdf._body("- Enterprise teams with existing Selenium infrastructure\n"
              "- Legacy browser support (IE11)\n- Java, Ruby, or C# primary language teams\n"
              "- Cloud grid providers at scale")

    # ── 4. CYPRESS ────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("4", "Cypress", FW_COLORS["cypress"])
    pdf._body(
        "Cypress is a JavaScript-based E2E framework that runs inside the browser alongside your "
        "app. Released in 2017, popular with React/frontend developers for its excellent DX, "
        "time-travel debugging, and automatic waiting.")

    pdf._sub_title("4.1 Architecture")
    pdf._body(
        "Cypress runs inside the browser (not externally like Selenium/Playwright):\n\n"
        "  Browser Process: [Cypress Test Runner] + [App iframe]\n"
        "  Node.js Server: proxy, file system, DB access\n\n"
        "Direct DOM access but limited to single-tab, with cross-origin restrictions.")

    pdf._sub_title("4.2 Key Features")
    for f in [
        "Time-Travel Debugging: DOM snapshots at every command",
        "Automatic Waiting: Commands auto-retry until assertions pass",
        "cy.intercept(): Network stubbing and mocking",
        "Component Testing: React, Vue, Angular, Svelte",
        "Screenshot & Video: Automatic capture on failure",
        "700+ Plugins: Large ecosystem",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("4.3 Code Example")
    pdf._code_block("""
describe('Product Search', () => {
  it('should find products', () => {
    cy.visit('https://myapp.com');
    cy.get('[data-testid="search"]').type('laptop');
    cy.get('[data-testid="search-btn"]').click();
    cy.get('.product-card').should('have.length', 5);
  });
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("4.4 Pros & Cons")
    pdf._pros_cons(
        pros=["Best developer experience", "Time-travel debugging", "Low flakiness",
              "Built-in mocking/stubs", "Component testing", "Excellent docs"],
        cons=["JS/TS only", "Limited multi-tab", "Cross-origin restrictions",
              "No native parallel (needs Cypress Cloud $)", "No Safari support"])

    pdf._check_space(20)
    pdf._sub_title("4.5 Best Suited For")
    pdf._body("- Frontend-heavy teams (React, Vue, Angular)\n"
              "- Projects prioritizing DX and fast iteration\n- Extensive API mocking needs")

    # ── 5. TOSCA ──────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("5", "Tricentis Tosca", FW_COLORS["tosca"])
    pdf._body(
        "Enterprise-grade, scriptless test automation platform. Model-based testing using UI "
        "models, reusable modules, and data-driven configs. Supports web, desktop, mobile, "
        "API, SAP, and mainframe testing.")

    pdf._sub_title("5.1 Architecture")
    pdf._body(
        "- Tosca Commander: Central IDE for test design and execution\n"
        "- Module Scanner: Scans UIs to build technical models\n"
        "- Test Data Service (TDS): Centralized test data management\n"
        "- Distributed Execution (DEX): Parallel execution across agents\n\n"
        "Workflow: SCAN -> BUILD -> DATA -> EXECUTE -> REPORT")

    pdf._sub_title("5.2 Key Features")
    for f in [
        "Model-Based / No-Code: QA testers without coding can create tests",
        "Multi-technology: Web, Desktop, Mobile, SAP, Salesforce, API, Mainframe",
        "Risk-Based Testing: Prioritize by business risk",
        "AI Self-healing: Intelligent locator maintenance",
        "SAP Specialization: Deep S/4HANA, Fiori, GUI integration",
        "Compliance: Audit trails, version control, regulatory",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(50)
    pdf._sub_title("5.3 Pros & Cons")
    pdf._pros_cons(
        pros=["No coding required", "Multi-technology coverage", "AI self-healing",
              "Enterprise compliance", "Best SAP testing", "Vendor SLA support"],
        cons=["Expensive ($30K-$100K+/year)", "Vendor lock-in", "Less flexible than code-based",
              "Slower execution", "Overkill for small projects"])

    pdf._check_space(20)
    pdf._sub_title("5.4 Best Suited For")
    pdf._body("- Large enterprises with SAP/Salesforce/Mainframe\n"
              "- Non-technical QA teams\n- Regulated industries needing audit trails")

    # ── 6. PUPPETEER ──────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("6", "Puppeteer", FW_COLORS["puppeteer"])
    pdf._body(
        "Google's Node.js library for Chromium automation via Chrome DevTools Protocol. "
        "Predecessor to Playwright. Excels at scraping, PDF generation, screenshots, "
        "and performance profiling.")

    pdf._sub_title("6.1 Key Features")
    for f in [
        "Direct CDP access: Fine-grained Chromium control",
        "PDF Generation: High-quality rendering from web pages",
        "Performance Profiling: Chrome tracing access",
        "Network Interception: Monitor/modify requests",
        "Auto-downloaded Chromium: Ships matching binary",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("6.2 Code Example")
    pdf._code_block("""
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://myapp.com');
  await page.type('#search', 'laptop');
  await page.click('#search-btn');
  await page.waitForSelector('.product-card');
  await page.screenshot({ path: 'results.png' });
  await browser.close();
})();
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("6.3 Pros & Cons")
    pdf._pros_cons(
        pros=["Most powerful Chromium control", "Great for scraping/PDFs", "Google-backed",
              "Large community", "Lightweight API"],
        cons=["Chromium-only", "No auto-wait", "No test runner", "JS only",
              "Being superseded by Playwright"])

    # ── 7. WEBDRIVERIO ────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("7", "WebDriverIO", FW_COLORS["webdriverio"])
    pdf._body(
        "Progressive Node.js framework on WebDriver + optional DevTools protocol. "
        "Supports web, mobile (Appium), and desktop from a single framework.")

    pdf._sub_title("7.1 Key Features")
    for f in [
        "Dual Protocol: WebDriver (W3C) and DevTools Protocol",
        "Mobile Testing: First-class Appium integration",
        "BDD: Works with Mocha, Jasmine, or Cucumber",
        "50+ Services: Visual testing, Appium, cloud grids",
        "Component Testing: React, Vue, Svelte, Lit",
    ]:
        pdf._check_space(8)
        pdf._bullet(f)

    pdf._check_space(40)
    pdf._sub_title("7.2 Code Example")
    pdf._code_block("""
describe('Product Search', () => {
  it('finds products', async () => {
    await browser.url('https://myapp.com');
    await $('[data-testid="search"]').setValue('laptop');
    await $('[data-testid="search-btn"]').click();
    await expect($$('.product-card')).toBeElementsArrayOfSize(5);
  });
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("7.3 Pros & Cons")
    pdf._pros_cons(
        pros=["Dual protocol flexibility", "Mobile via Appium", "BDD/Cucumber support",
              "Cloud grids built-in", "Active community"],
        cons=["JS/TS only", "Complex configuration", "Slower than Playwright",
              "Inherits WebDriver flakiness"])

    # ── 8. TESTCAFE ───────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("8", "TestCafe", FW_COLORS["testcafe"])
    pdf._body(
        "Zero-config Node.js E2E framework. No WebDriver needed - injects test scripts via "
        "URL-rewriting proxy. Works with any browser that can open a URL.")

    pdf._sub_title("8.1 Key Features & Code Example")
    for f in ["Zero Config: No drivers or plugins", "Any Browser: Including remote mobile",
              "Role-based Auth: Login state reuse built-in", "Live Mode: Instant re-runs on save"]:
        pdf._bullet(f)

    pdf._code_block("""
import { Selector } from 'testcafe';
fixture('Search').page('https://myapp.com');

test('finds products', async t => {
  await t
    .typeText('[data-testid="search"]', 'laptop')
    .click('[data-testid="search-btn"]')
    .expect(Selector('.product-card').count).eql(5);
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("8.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Zero setup", "Works with any browser", "Built-in auto-wait",
              "Role-based auth", "Free and open source"],
        cons=["JS/TS only", "Proxy can cause subtle issues", "Smaller community",
              "DevExpress shifting focus"])

    # ── 9. ROBOT FRAMEWORK ────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("9", "Robot Framework", FW_COLORS["robot"])
    pdf._body(
        "Python-based keyword-driven automation framework for acceptance testing and RPA. "
        "Originally from Nokia Networks (2005). Extensible with 400+ libraries.")

    pdf._sub_title("9.1 Key Features & Code Example")
    for f in ["Keyword-Driven: Human-readable test cases", "400+ Libraries: Web, API, DB, SSH, RPA",
              "BDD Support: Given/When/Then syntax", "Parallel via Pabot"]:
        pdf._bullet(f)

    pdf._code_block("""
*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
User Can Search
    Open Browser    https://myapp.com    chrome
    Input Text      [data-testid="search"]    laptop
    Click Button    [data-testid="search-btn"]
    Wait Until Element Is Visible    css:.product-card
    ${count}=    Get Element Count    css:.product-card
    Should Be Equal As Numbers    ${count}    5
    [Teardown]    Close Browser
""", "robot")

    pdf._check_space(50)
    pdf._sub_title("9.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Readable by non-technical people", "Highly extensible", "Multi-domain",
              "Good for RPA", "Free and open source"],
        cons=["Tabular syntax limiting for complex logic", "Slower execution",
              "Debugging keyword failures is hard", "Depends on SeleniumLibrary for web"])

    # ── 10. NIGHTWATCH ────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("10", "Nightwatch.js", FW_COLORS["nightwatch"])
    pdf._body(
        "Integrated Node.js E2E framework with built-in test runner, assertions, "
        "and page objects. V3 added component testing for React, Vue, and Angular.")

    pdf._sub_title("10.1 Code Example")
    pdf._code_block("""
describe('Search', function() {
  it('finds products', function(browser) {
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
    pdf._sub_title("10.2 Pros & Cons")
    pdf._pros_cons(
        pros=["All-in-one: runner + assertions + reporter", "Simple API", "Component testing",
              "Page Object Model built-in"],
        cons=["JS/TS only", "Smaller community", "WebDriver-based flakiness",
              "Fewer integrations than WDIO"])

    # ── 11. APPIUM ────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("11", "Appium", FW_COLORS["appium"])
    pdf._body(
        "Open-source mobile automation for native, hybrid, and mobile web apps on iOS and "
        "Android. Extends WebDriver protocol to mobile. Appium 2.0 uses a driver/plugin architecture.")

    pdf._sub_title("11.1 Architecture")
    pdf._body(
        "  Test Script --> Appium Server (Node.js) --> Platform Driver --> Device\n\n"
        "Drivers: XCUITest (iOS), UiAutomator2 (Android), Espresso (Android), "
        "Mac2 (macOS), Windows (desktop)")

    pdf._sub_title("11.2 Code Example")
    pdf._code_block("""
from appium import webdriver
from appium.options import UiAutomator2Options

options = UiAutomator2Options()
options.platform_name = 'Android'
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
    pdf._sub_title("11.3 Pros & Cons")
    pdf._pros_cons(
        pros=["Cross-platform mobile", "WebDriver-compatible API", "Multi-language",
              "Real devices + simulators", "Cloud device farm integration"],
        cons=["Slow execution", "Complex setup", "Flaky on real devices",
              "iOS requires macOS", "Steep learning curve"])

    # ── 12. KATALON ───────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("12", "Katalon Studio", FW_COLORS["katalon"])
    pdf._body(
        "Low-code test automation platform for web, API, mobile, and desktop. Built on Selenium "
        "and Appium with a visual IDE, record-and-playback, and Groovy scripting.")

    pdf._sub_title("12.1 Key Features")
    for f in ["Dual Mode: Visual (keyword-driven) + Script (Groovy)", "Record & Playback",
              "Web + API + Mobile in one tool", "Self-healing locators", "Free tier available"]:
        pdf._bullet(f)

    pdf._check_space(50)
    pdf._sub_title("12.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Low barrier to entry", "Multi-platform in one tool", "Free tier",
              "Good CI/CD integration", "Self-healing"],
        cons=["Groovy language (niche)", "Slower than pure Selenium", "Paid advanced features",
              "Vendor lock-in", "Heavy IDE"])

    # ── 13. JEST + TESTING LIBRARY ────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("13", "Jest + Testing Library", FW_COLORS["jest"])
    pdf._body(
        "Jest (Facebook) + Testing Library (Kent C. Dodds) are the dominant solution for React "
        "component testing. Tests components in jsdom (virtual DOM), NOT real browsers. "
        "Testing Library also supports Vue, Angular, Svelte.")

    pdf._sub_title("13.1 Code Example")
    pdf._code_block("""
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProductSearch from './ProductSearch';

test('user can search', async () => {
  render(<ProductSearch />);
  const input = screen.getByRole('searchbox');
  await userEvent.type(input, 'laptop');
  await userEvent.click(screen.getByRole('button', { name: /search/i }));
  const cards = await screen.findAllByTestId('product-card');
  expect(cards).toHaveLength(5);
});
""", "jsx")

    pdf._check_space(50)
    pdf._sub_title("13.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Fastest feedback (no browser)", "User-centric testing", "Built-in mocking/coverage",
              "Zero config with CRA/Vite/Next", "Works across React/Vue/Angular/Svelte"],
        cons=["NOT E2E (no real browser)", "jsdom limitations", "Cannot test visual/CSS",
              "Snapshots can be noisy", "JS/TS only"])

    # ── 14. K6 ────────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("14", "k6 (Performance Testing)", FW_COLORS["k6"])
    pdf._body(
        "Load and performance testing tool by Grafana Labs. Written in Go with JavaScript "
        "scripting API. Designed for developers who want performance tests as code.")

    pdf._sub_title("14.1 Code Example")
    pdf._code_block("""
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m',  target: 50 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('https://myapp.com/api/products');
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("14.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Developer-friendly (JS tests-as-code)", "Efficient Go runtime",
              "Grafana integration", "Multi-protocol (HTTP, WebSocket, gRPC)", "Free and open source"],
        cons=["Not functional E2E", "JS only", "No HTML report built-in",
              "Cloud features are paid"])

    # ── 15. DETOX ─────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("15", "Detox (React Native)", FW_COLORS["detox"])
    pdf._body(
        "Gray-box E2E testing for React Native by Wix. Synchronizes with React Native "
        "runtime (animations, network, JS) to dramatically reduce flakiness vs Appium.")

    pdf._sub_title("15.1 Code Example")
    pdf._code_block("""
describe('Search', () => {
  beforeAll(async () => { await device.launchApp(); });

  it('finds products', async () => {
    await element(by.id('search-input')).typeText('laptop');
    await element(by.id('search-btn')).tap();
    await waitFor(element(by.id('product-card')))
      .toBeVisible().withTimeout(5000);
  });
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("15.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Gray-box sync - much less flaky", "Fast native execution",
              "Jest integration", "Built for React Native"],
        cons=["React Native only", "iOS needs macOS", "Complex setup",
              "JS/TS only", "No cloud device farms"])

    # ── 16. GAUGE ─────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("16", "Gauge", FW_COLORS["gauge"])
    pdf._body(
        "Open-source BDD framework by ThoughtWorks. Markdown-based specs that are "
        "human-readable and executable. Multi-language: Java, C#, Python, JS, Ruby, Go.")

    pdf._sub_title("16.1 Code Example")
    pdf._code_block("""
# Product Search Specification

## User searches for products
* Navigate to "https://myapp.com"
* Type "laptop" in search box
* Click search button
* Verify "5" products are displayed
""", "markdown (.spec)")

    pdf._check_space(50)
    pdf._sub_title("16.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Markdown specs readable by business", "6+ languages", "Built by ThoughtWorks",
              "Parallel execution built-in"],
        cons=["Smaller community than Cucumber", "Needs separate browser library",
              "Step matching can be fragile"])

    # ── 17. KARATE DSL ───────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("17", "Karate DSL", FW_COLORS["karate"])
    pdf._body(
        "API + UI + Performance testing in one JVM framework. Gherkin-like BDD syntax "
        "that's directly executable without step definitions.")

    pdf._sub_title("17.1 Code Example")
    pdf._code_block("""
Feature: Product Search API

  Scenario: Search returns products
    Given url 'https://myapp.com/api/products'
    And param q = 'laptop'
    When method get
    Then status 200
    And match response.length == 5
    And match each response contains { name: '#string', price: '#number' }
""", "gherkin (.feature)")

    pdf._check_space(50)
    pdf._sub_title("17.2 Pros & Cons")
    pdf._pros_cons(
        pros=["API + UI + Performance in one tool", "No step definitions needed",
              "Built-in mock server", "Native JSON/XML assertions", "Free (MIT)"],
        cons=["JVM only", "UI testing less mature", "Smaller community"])

    # ── 18. CODECEPTJS ────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("18", "CodeceptJS", FW_COLORS["codeceptjs"])
    pdf._body(
        "Abstraction layer over Playwright/Puppeteer/WebDriverIO/TestCafe. "
        "Write tests once, switch backends without rewriting.")

    pdf._sub_title("18.1 Code Example")
    pdf._code_block("""
Feature('Product Search');

Scenario('user finds products', ({ I }) => {
  I.amOnPage('https://myapp.com');
  I.fillField('[data-testid="search"]', 'laptop');
  I.click('[data-testid="search-btn"]');
  I.seeNumberOfElements('.product-card', 5);
});
""", "javascript")

    pdf._check_space(50)
    pdf._sub_title("18.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Backend-agnostic", "Highly readable BDD syntax", "Interactive debug shell",
              "AI self-healing locators"],
        cons=["JS/TS only", "Extra abstraction overhead", "Some driver features not exposed"])

    # ── 19. WATIR ─────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("19", "Watir", FW_COLORS["watir"])
    pdf._body("Ruby library for web browser automation (since 2001). Clean Ruby-like API "
              "built on Selenium WebDriver.")

    pdf._sub_title("19.1 Code Example")
    pdf._code_block("""
require 'watir'
browser = Watir::Browser.new :chrome
browser.goto 'https://myapp.com'
browser.text_field(data_testid: 'search').set 'laptop'
browser.button(data_testid: 'search-btn').click
browser.divs(class: 'product-card').wait_until(size: 5)
browser.close
""", "ruby")

    pdf._check_space(50)
    pdf._sub_title("19.2 Pros & Cons")
    pdf._pros_cons(
        pros=["Beautiful Ruby API", "Built-in waits", "Mature and stable"],
        cons=["Ruby only", "Inherits Selenium limitations", "Development slowed",
              "No modern features (tracing, mocking)"])

    # ── 20. PROTRACTOR ────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("20", "Protractor (Deprecated)", FW_COLORS["protractor"])
    pdf._body(
        "DEPRECATED (end-of-life August 2023). Was the official Angular E2E framework built on "
        "Selenium. The Angular team now recommends Playwright or Cypress.\n\n"
        "Migration paths:\n"
        "- Playwright: Official guide at playwright.dev. Budget 2-3 weeks.\n"
        "- Cypress: Angular CLI now offers Cypress via `ng e2e`.\n"
        "- Do NOT start new projects with Protractor.")

    # ── 21. COMPARISON ────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("21", "Head-to-Head Comparison")

    pdf._sub_title("21.1 Browser E2E Comparison")
    pdf._table(
        ["Feature", "Playwright", "Selenium", "Cypress", "Puppeteer", "WDIO"],
        [
            ["Languages",     "JS/Py/Java/C#", "6+",     "JS/TS",  "JS/TS",  "JS/TS"],
            ["Chrome",        "Yes", "Yes", "Yes", "Yes", "Yes"],
            ["Firefox",       "Yes", "Yes", "Yes", "Exp.", "Yes"],
            ["Safari",        "Yes", "Yes", "Exp.", "No", "Yes"],
            ["Auto-wait",     "Built-in", "Manual", "Built-in", "Manual", "Built-in"],
            ["Network Mock",  "Native", "Proxy", "Native", "Native", "Native"],
            ["Parallel",      "Built-in", "Grid", "Cloud($)", "Manual", "Built-in"],
            ["API Testing",   "Built-in", "No", "cy.request", "No", "No"],
            ["Debugging",     "Trace", "Logs", "Time-Travel", "CDP", "Logs"],
        ],
        [30, 30, 28, 28, 28, 30])

    pdf._sub_title("21.2 Specialized Frameworks")
    pdf._table(
        ["Framework", "Type", "Language", "Best For"],
        [
            ["Tosca",    "Enterprise", "Scriptless", "SAP, compliance"],
            ["Katalon",  "Low-code",   "Groovy",     "Mixed-skill QA"],
            ["Robot",    "Keyword",    "Python",     "BDD + multi-domain"],
            ["Appium",   "Mobile",     "Multi",      "Native mobile apps"],
            ["Detox",    "Mobile",     "JS/TS",      "React Native"],
            ["k6",       "Performance","JS",         "Load testing"],
            ["Jest+RTL", "Component",  "JS/TS",      "React components"],
            ["Karate",   "API+UI",     "JVM",        "API testing"],
            ["Gauge",    "BDD",        "Multi",      "Markdown specs"],
            ["CodeceptJS","E2E",       "JS/TS",      "Backend-agnostic"],
        ],
        [30, 30, 28, 86])

    pdf._check_space(60)
    pdf._sub_title("21.3 Performance Benchmarks (Indicative)")
    pdf._dim_body("Note: Varies by machine and application. Representative values.")
    pdf._table(
        ["Metric", "Playwright", "Selenium", "Cypress", "Puppeteer"],
        [
            ["Cold start",     "~2s",    "~3-5s",  "~4-6s",  "~1.5s"],
            ["Navigation test","~200ms", "~500ms", "~350ms", "~180ms"],
            ["Form submit",    "~400ms", "~1000ms","~600ms", "~350ms"],
            ["Memory/browser", "~150MB", "~200MB", "~300MB", "~140MB"],
        ],
        [44, 32, 32, 32, 32])

    # ── 22. SETUP QUICK START ─────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("22", "Setup & Quick Start Guide")

    setups = [
        ("22.1 Playwright", "npm init -y && npm install -D @playwright/test\nnpx playwright install\nnpx playwright test", "bash"),
        ("22.2 Selenium (Python)", "pip install selenium pytest\npytest  # Selenium Manager auto-downloads drivers", "bash"),
        ("22.3 Cypress", "npm init -y && npm install -D cypress\nnpx cypress open      # Interactive\nnpx cypress run       # Headless", "bash"),
        ("22.4 Puppeteer", "npm install puppeteer\nnode test.js  # Chromium auto-downloaded", "bash"),
        ("22.5 WebDriverIO", "npm init wdio@latest   # Interactive wizard\nnpx wdio run wdio.conf.js", "bash"),
        ("22.6 TestCafe", "npm install -D testcafe\nnpx testcafe chrome tests/", "bash"),
        ("22.7 Robot Framework", "pip install robotframework robotframework-seleniumlibrary\nrobot tests/", "bash"),
        ("22.8 k6", "# macOS: brew install k6\n# Windows: choco install k6\nk6 run script.js", "bash"),
        ("22.9 Appium", "npm install -g appium\nappium driver install uiautomator2\nappium", "bash"),
    ]
    for title, code, lang in setups:
        pdf._check_space(35)
        pdf._sub_title(title)
        pdf._code_block(code, lang)

    # ── 23. CI/CD ─────────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("23", "CI/CD Integration Patterns")

    pdf._sub_title("23.1 GitHub Actions - Playwright")
    pdf._code_block("""
name: E2E Tests
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
name: E2E Tests
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

    pdf._sub_title("23.3 Docker Execution")
    pdf._code_block("""
# Playwright
FROM mcr.microsoft.com/playwright:v1.42.0-jammy
WORKDIR /app
COPY . .
RUN npm ci
CMD ["npx", "playwright", "test"]
""", "dockerfile")

    # ── 24. DECISION FRAMEWORK ────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("24", "Decision Framework")

    pdf._sub_title("24.1 Quick Decision Tree")
    decisions = [
        ("What type of testing?", "Performance -> k6 | Mobile -> Appium/Detox | API -> Karate | Web E2E -> Continue"),
        ("Need SAP/Desktop/Mainframe?", "YES -> Tosca | NO -> Continue"),
        ("Non-technical QA team?", "YES -> Tosca or Katalon | NO -> Continue"),
        ("React Native app?", "YES -> Detox | NO -> Continue"),
        ("Need IE11?", "YES -> Selenium | NO -> Continue"),
        ("Need Safari/WebKit?", "YES -> Playwright | NO -> Continue"),
        ("Top priority is DX?", "YES -> Cypress | NO -> Continue"),
        ("Need Python/Java/C#?", "YES -> Playwright or Selenium | NO -> Continue"),
        ("New project from scratch?", "YES -> Playwright (recommended) | NO -> Evaluate migration"),
    ]
    for q, a in decisions:
        pdf._check_space(16)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*t["text"])
        pdf.cell(0, 6, f"Q: {q}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*t["accent_light"])
        pdf.cell(0, 6, f"   {a}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf._check_space(50)
    pdf._sub_title("24.2 Recommendation Summary")
    pdf._table(
        ["Scenario", "Recommended", "Runner-up"],
        [
            ["New project, any stack",   "Playwright",  "Cypress"],
            ["Frontend React/Vue",       "Cypress",     "Playwright"],
            ["Enterprise, SAP",          "Tosca",       "Katalon"],
            ["Python/Java backend",      "Playwright",  "Selenium"],
            ["Mobile native apps",       "Appium",      "Detox (RN)"],
            ["API + contract testing",   "Karate",      "Playwright"],
            ["Performance testing",      "k6",          "Artillery"],
            ["Component testing",        "Jest + RTL",  "Vitest"],
            ["BDD acceptance",           "Gauge",       "Robot Framework"],
            ["Budget-conscious startup", "Playwright",  "Cypress"],
        ],
        [50, 40, 84])

    # ── 25. GLOSSARY ──────────────────────────────────────────────────────
    pdf._new_page()
    pdf._section_title("25", "Glossary & Resources")

    pdf._sub_title("25.1 Glossary")
    terms = [
        ("E2E Testing", "Testing the complete flow from the user's perspective"),
        ("CDP", "Chrome DevTools Protocol - low-level Chromium API"),
        ("W3C WebDriver", "Official web standard for browser automation"),
        ("Flaky Test", "Test that passes and fails intermittently"),
        ("Auto-wait", "Framework waits for elements to be ready automatically"),
        ("Headless", "Browser running without visible UI (for CI/CD)"),
        ("Page Object Model", "Design pattern encapsulating page interactions"),
        ("Gray-box Testing", "Testing with some app internal knowledge (Detox)"),
        ("Load Testing", "Testing system under expected load (k6)"),
        ("BDD", "Behavior-Driven Development - spec-first testing"),
    ]
    for term, defn in terms:
        pdf._check_space(12)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*t["accent_light"])
        pdf.cell(0, 6, term, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*t["text"])
        pdf.cell(0, 5, f"  {defn}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf._check_space(50)
    pdf._sub_title("25.2 Official Resources")
    resources = [
        ("Playwright", "playwright.dev"), ("Selenium", "selenium.dev/documentation"),
        ("Cypress", "docs.cypress.io"), ("Tosca", "documentation.tricentis.com"),
        ("Puppeteer", "pptr.dev"), ("WebDriverIO", "webdriver.io"),
        ("TestCafe", "testcafe.io/documentation"), ("Robot Framework", "robotframework.org"),
        ("Appium", "appium.io/docs"), ("Katalon", "docs.katalon.com"),
        ("Jest", "jestjs.io"), ("Testing Library", "testing-library.com"),
        ("k6", "k6.io/docs"), ("Detox", "wix.github.io/Detox"),
        ("Gauge", "docs.gauge.org"), ("Karate", "karatelabs.github.io/karate"),
        ("CodeceptJS", "codecept.io"),
    ]
    for name, url in resources:
        pdf._check_space(8)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*t["text"])
        pdf.cell(40, 6, name)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*t["accent_light"])
        pdf.cell(0, 6, url, new_x="LMARGIN", new_y="NEXT")


# ═══════════════════════════════════════════════════════════════════════════════
# Main — generate PDFs
# ═══════════════════════════════════════════════════════════════════════════════

def generate_pdf(theme: dict, output_path: str) -> str:
    """Generate a single themed PDF."""
    pdf = TestingFrameworkDoc(theme)
    build_content(pdf)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f"  Generated: {output_path} ({pdf.page_no()} pages)")
    return output_path


def main():
    mode = "both"
    if len(sys.argv) > 1 and sys.argv[1] == "--theme":
        mode = sys.argv[2] if len(sys.argv) > 2 else "both"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, "docs")

    print("\nGenerating Testing Frameworks Guide PDFs...")
    print("=" * 50)

    if mode in ("dark", "both"):
        generate_pdf(DARK_THEME, os.path.join(docs_dir, "testing-frameworks-guide-dark.pdf"))

    if mode in ("light", "both"):
        generate_pdf(LIGHT_THEME, os.path.join(docs_dir, "testing-frameworks-guide-light.pdf"))

    print("=" * 50)
    print("Done!\n")


if __name__ == "__main__":
    main()
