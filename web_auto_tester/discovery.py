"""
Framework-agnostic site crawler.

Discovers pages by following links, router outlets, and SPA navigation patterns.
Auto-detects the JS framework running on each page.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page, BrowserContext

from .models import DiscoveredPage, FrameworkInfo, DetectedFramework


# ---------------------------------------------------------------------------
# Framework detection JS - runs in browser context
# ---------------------------------------------------------------------------
DETECT_FRAMEWORK_JS = """
() => {
    const info = {
        name: 'unknown',
        version: null,
        isSpa: false,
        isSsr: false,
        features: [],
        signals: {},
    };

    // ---- Angular ----
    const ngEl = document.querySelector('[ng-version]');
    if (ngEl) {
        info.name = 'angular';
        info.version = ngEl.getAttribute('ng-version');
        info.isSpa = true;
    }
    if (window.getAllAngularTestabilities || window.ng) {
        info.name = 'angular';
        info.isSpa = true;
    }
    // AngularJS (legacy)
    if (window.angular && window.angular.version) {
        info.name = 'angular';
        info.version = window.angular.version.full;
        info.isSpa = true;
        info.signals.legacy = true;
    }

    // ---- React ----
    if (info.name === 'unknown') {
        const reactRoot = document.querySelector('[data-reactroot]')
            || document.getElementById('__next')
            || document.getElementById('root');
        if (reactRoot) {
            // Check for React fiber
            const keys = Object.keys(reactRoot);
            const hasFiber = keys.some(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
            if (hasFiber) {
                info.name = 'react';
                info.isSpa = true;
            }
        }
        if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
            info.name = info.name === 'unknown' ? 'react' : info.name;
        }
        if (window.__NEXT_DATA__) {
            info.name = 'nextjs';
            info.isSpa = true;
            info.isSsr = true;
            info.version = window.__NEXT_DATA__?.buildId || null;
        }
        if (document.getElementById('__gatsby')) {
            info.name = 'gatsby';
            info.isSpa = true;
            info.isSsr = true;
        }
    }

    // ---- Vue ----
    if (info.name === 'unknown') {
        const vueEl = document.querySelector('[data-v-app]')
            || document.getElementById('__nuxt')
            || document.getElementById('app');
        if (vueEl && (vueEl.__vue_app__ || vueEl.__vue__)) {
            info.name = 'vue';
            info.isSpa = true;
            if (vueEl.__vue_app__) {
                info.version = vueEl.__vue_app__.version || '3.x';
            } else if (vueEl.__vue__) {
                info.version = '2.x';
            }
        }
        if (window.__NUXT__) {
            info.name = 'nuxt';
            info.isSpa = true;
            info.isSsr = true;
        }
        if (window.Vue) {
            info.name = info.name === 'unknown' ? 'vue' : info.name;
            info.version = info.version || (window.Vue.version || null);
        }
    }

    // ---- Svelte ----
    if (info.name === 'unknown') {
        const svelteEls = document.querySelectorAll('[class*="svelte-"]');
        if (svelteEls.length > 0) {
            info.name = 'svelte';
            info.isSpa = true;
        }
        if (window.__sveltekit) {
            info.name = 'svelte';
            info.isSpa = true;
            info.isSsr = true;
            info.features.push('SvelteKit');
        }
    }

    // ---- Ember ----
    if (info.name === 'unknown' && window.Ember) {
        info.name = 'ember';
        info.version = window.Ember.VERSION || null;
        info.isSpa = true;
    }

    // ---- jQuery (not a framework, but useful to know) ----
    if (window.jQuery || window.$?.fn?.jquery) {
        const jqVer = window.jQuery?.fn?.jquery || window.$?.fn?.jquery;
        if (info.name === 'unknown') {
            info.name = 'jquery';
            info.version = jqVer || null;
        } else {
            info.features.push('jQuery ' + (jqVer || ''));
        }
    }

    // ---- Feature detection (framework-agnostic) ----
    // Router
    if (document.querySelector('router-outlet, [routerlink], [routerLink]'))
        info.features.push('Angular Router');
    if (window.__NEXT_DATA__ || document.querySelector('[data-nextjs-page]'))
        info.features.push('Next.js Router');
    if (window.__NUXT__ || document.querySelector('.nuxt-link'))
        info.features.push('Nuxt Router');

    // State management
    if (window.__REDUX_DEVTOOLS_EXTENSION__) info.features.push('Redux');
    if (window.__MOBX_DEVTOOLS_GLOBAL_HOOK__) info.features.push('MobX');
    if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__) info.features.push('Vue DevTools');
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) info.features.push('React DevTools');

    // UI libraries
    if (document.querySelector('mat-toolbar, mat-card, mat-sidenav, [mat-raised-button]'))
        info.features.push('Angular Material');
    if (document.querySelector('.MuiButton-root, .MuiPaper-root, .css-1'))
        info.features.push('MUI / Material UI');
    if (document.querySelector('.ant-btn, .ant-layout, .ant-card'))
        info.features.push('Ant Design');
    if (document.querySelector('.chakra-button, [data-chakra-component]'))
        info.features.push('Chakra UI');
    if (document.querySelector('[class*="tailwind"], [class*="tw-"]'))
        info.features.push('Tailwind CSS');
    if (document.querySelector('.bootstrap, .btn-primary, .container-fluid'))
        info.features.push('Bootstrap');
    if (document.querySelector('.p-button, .p-component'))
        info.features.push('PrimeNG / PrimeReact');

    // Service Worker / PWA
    if (navigator.serviceWorker?.controller) info.features.push('Service Worker');

    // SPA detection fallback
    if (!info.isSpa) {
        const hasHistoryApi = !!document.querySelector(
            'a[routerlink], a[href^="/"][onclick], [data-link]'
        );
        if (hasHistoryApi) info.isSpa = true;
    }

    return info;
}
"""


class SiteCrawler:
    """Crawls any SPA or MPA site to discover navigable routes."""

    def __init__(
        self,
        base_url: str,
        max_pages: int = 50,
        max_depth: int = 4,
        exclude_patterns: list[str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.exclude_patterns = exclude_patterns or [
            r"/api/",
            r"\.(pdf|zip|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|css|js|map)(\?|$)",
            r"mailto:",
            r"tel:",
            r"javascript:",
            r"#$",
            r"oauth|callback|logout|signout|login|signin|auth",
        ]
        self._visited: set[str] = set()
        self._pages: list[DiscoveredPage] = []
        self._base_domain = urlparse(base_url).netloc

    async def crawl(self, context: BrowserContext) -> list[DiscoveredPage]:
        """Crawl the site starting from base_url."""
        page = await context.new_page()
        try:
            await self._visit_page(page, self.base_url, depth=0, found_on="entry")
        finally:
            await page.close()
        return self._pages

    async def _visit_page(
        self, page: Page, url: str, depth: int, found_on: str
    ) -> None:
        normalized = self._normalize_url(url)
        if normalized in self._visited:
            return
        if len(self._pages) >= self.max_pages:
            return
        if depth > self.max_depth:
            return
        if self._should_exclude(url):
            return

        self._visited.add(normalized)

        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            status_code = response.status if response else 0

            # Give SPA frameworks time to hydrate/render
            await page.wait_for_timeout(2000)

            # Detect framework
            fw_info = await self._detect_framework(page)

            title = await page.title()

            discovered = DiscoveredPage(
                url=normalized,
                title=title,
                status_code=status_code,
                framework=fw_info,
                depth=depth,
                found_on=found_on,
            )
            self._pages.append(discovered)

            # Extract links for further crawling
            if depth < self.max_depth:
                links = await self._extract_links(page)
                for link in links:
                    if len(self._pages) >= self.max_pages:
                        break
                    await self._visit_page(page, link, depth + 1, normalized)

        except Exception:
            discovered = DiscoveredPage(
                url=normalized,
                title="(Failed to load)",
                status_code=0,
                depth=depth,
                found_on=found_on,
            )
            self._pages.append(discovered)

    async def _extract_links(self, page: Page) -> list[str]:
        """Extract all internal links - works for any framework."""
        links: list[str] = []
        try:
            raw_links = await page.evaluate("""
                () => {
                    const seen = new Set();
                    const collect = (selector, attr) => {
                        document.querySelectorAll(selector).forEach(el => {
                            const val = el.getAttribute(attr);
                            if (val && !seen.has(val)) { seen.add(val); }
                        });
                    };
                    // Standard links
                    collect('a[href]', 'href');
                    // Angular
                    collect('[routerlink]', 'routerlink');
                    collect('[routerLink]', 'routerLink');
                    collect('[ng-reflect-router-link]', 'ng-reflect-router-link');
                    // Nuxt / Next
                    collect('a[data-nuxt-link]', 'href');
                    collect('a[data-nlink]', 'href');
                    // Generic nav patterns
                    collect('nav a', 'href');
                    collect('.sidebar a', 'href');
                    collect('.menu a', 'href');
                    collect('[role="menuitem"] a', 'href');
                    collect('[role="navigation"] a', 'href');
                    return [...seen];
                }
            """)

            for href in raw_links:
                full_url = self._resolve_url(href)
                if full_url and self._is_internal(full_url):
                    links.append(full_url)

        except Exception:
            pass

        return links

    async def _detect_framework(self, page: Page) -> FrameworkInfo:
        """Detect the JS framework running on the page."""
        try:
            raw = await page.evaluate(DETECT_FRAMEWORK_JS)
        except Exception:
            return FrameworkInfo()

        name_map = {
            "angular": DetectedFramework.ANGULAR,
            "react": DetectedFramework.REACT,
            "vue": DetectedFramework.VUE,
            "svelte": DetectedFramework.SVELTE,
            "nextjs": DetectedFramework.NEXTJS,
            "nuxt": DetectedFramework.NUXT,
            "gatsby": DetectedFramework.GATSBY,
            "ember": DetectedFramework.EMBER,
            "jquery": DetectedFramework.JQUERY,
        }

        return FrameworkInfo(
            name=name_map.get(raw.get("name", ""), DetectedFramework.UNKNOWN),
            version=raw.get("version"),
            is_spa=raw.get("isSpa", False),
            is_ssr=raw.get("isSsr", False),
            features=raw.get("features", []),
            raw_signals=raw.get("signals", {}),
        )

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _resolve_url(self, href: str) -> str | None:
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return None
        if href.startswith("http"):
            return href
        return urljoin(self.base_url + "/", href)

    def _is_internal(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == self._base_domain

    def _should_exclude(self, url: str) -> bool:
        for pattern in self.exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
