"""
Framework-agnostic test analyzers.

Each analyzer is an async function that takes a Playwright Page + DiscoveredPage
and returns a list of TestResult objects. None of these are tied to a specific
JS framework - the framework health analyzer adapts based on what was detected.
"""

from __future__ import annotations

import time

from playwright.async_api import Page, Response, ConsoleMessage

from .models import (
    TestResult, TestStatus, TestCategory,
    DiscoveredPage, DetectedFramework,
)


# ---------------------------------------------------------------------------
# 1. PAGE LOAD
# ---------------------------------------------------------------------------
async def analyze_page_load(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    url = discovered.url

    start = time.perf_counter()
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        elapsed = (time.perf_counter() - start) * 1000
        status = response.status if response else 0

        if 200 <= status < 300:
            results.append(TestResult(
                name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
                status=TestStatus.PASSED, message=f"Page returned {status}",
                details={"status_code": status}, duration_ms=elapsed,
            ))
        elif 300 <= status < 400:
            results.append(TestResult(
                name="HTTP Redirect", category=TestCategory.PAGE_LOAD,
                status=TestStatus.WARNING, message=f"Redirect {status}",
                details={"status_code": status}, duration_ms=elapsed,
            ))
        else:
            results.append(TestResult(
                name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
                status=TestStatus.FAILED, message=f"Error status {status}",
                details={"status_code": status}, duration_ms=elapsed,
            ))
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        results.append(TestResult(
            name="HTTP Status OK", category=TestCategory.PAGE_LOAD,
            status=TestStatus.FAILED, message=f"Failed to load: {e}",
            duration_ms=elapsed,
        ))
        return results

    await page.wait_for_timeout(1500)

    # Content check
    body_len = await page.evaluate("() => document.body?.innerText?.trim()?.length || 0")
    results.append(TestResult(
        name="Page Has Content", category=TestCategory.PAGE_LOAD,
        status=TestStatus.PASSED if body_len > 10 else TestStatus.WARNING,
        message=f"{body_len} chars of text content" if body_len > 10
                else "Very little or no visible content",
        details={"text_length": body_len},
    ))

    # Title
    title = await page.title()
    results.append(TestResult(
        name="Page Has Title", category=TestCategory.PAGE_LOAD,
        status=TestStatus.PASSED if title and title.strip() else TestStatus.WARNING,
        message=f"Title: '{title}'" if title else "No page title",
        details={"title": title},
    ))

    # Error-page detection (generic)
    error_indicators = await page.evaluate("""
        () => {
            const t = document.body?.innerText?.toLowerCase() || '';
            const hits = [];
            if (t.includes('404') && (t.includes('not found') || t.includes('page not found')))
                hits.push('404 Not Found');
            if (t.includes('500') && t.includes('server error')) hits.push('500 Server Error');
            if (t.includes('application error')) hits.push('Application Error');
            if (t.includes('chunk load') || t.includes('chunkloaderror'))
                hits.push('Chunk Load Error');
            if (t.includes('hydration') && t.includes('error'))
                hits.push('Hydration Error');
            if (t.includes('uncaught') && t.includes('error'))
                hits.push('Uncaught Error');
            return hits;
        }
    """)
    results.append(TestResult(
        name="No Error Page Displayed", category=TestCategory.PAGE_LOAD,
        status=TestStatus.FAILED if error_indicators else TestStatus.PASSED,
        message=f"Errors: {', '.join(error_indicators)}" if error_indicators
                else "No error page indicators found",
        details={"errors": error_indicators} if error_indicators else {},
    ))

    return results


# ---------------------------------------------------------------------------
# 2. CONSOLE ERRORS
# ---------------------------------------------------------------------------
async def analyze_console_errors(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    errors: list[str] = []
    warnings: list[str] = []

    def on_console(msg: ConsoleMessage) -> None:
        if msg.type == "error":
            errors.append(msg.text)
        elif msg.type == "warning":
            warnings.append(msg.text)

    page.on("console", on_console)
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
    except Exception:
        pass
    finally:
        page.remove_listener("console", on_console)

    NOISE = ["favicon", "third-party", "analytics", "gtm", "facebook",
             "google-analytics", "hotjar", "intercom", "clarity", "sentry"]
    real_errors = [e for e in errors if not any(n in e.lower() for n in NOISE)]

    results: list[TestResult] = []
    results.append(TestResult(
        name="No JS Console Errors", category=TestCategory.CONSOLE_ERRORS,
        status=TestStatus.FAILED if real_errors else TestStatus.PASSED,
        message=f"{len(real_errors)} JS error(s)" if real_errors
                else "No JavaScript errors in console",
        details={"errors": real_errors[:10], "total": len(real_errors)} if real_errors
                else {"warning_count": len(warnings)},
    ))

    if len(warnings) > 20:
        results.append(TestResult(
            name="Console Warnings", category=TestCategory.CONSOLE_ERRORS,
            status=TestStatus.WARNING,
            message=f"High warning count: {len(warnings)}",
            details={"sample": warnings[:5]},
        ))

    return results


# ---------------------------------------------------------------------------
# 3. BROKEN LINKS
# ---------------------------------------------------------------------------
async def analyze_links(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1000)
    except Exception:
        return results

    links = await page.evaluate("""
        () => [...document.querySelectorAll('a[href]')].map(a => ({
            href: a.href,
            text: a.innerText?.trim()?.substring(0, 50) || '(no text)',
            isExternal: a.hostname !== window.location.hostname,
        })).filter(l => l.href
            && !l.href.startsWith('javascript:')
            && !l.href.startsWith('mailto:')
            && !l.href.startsWith('tel:'))
    """)

    internal = [l for l in links if not l["isExternal"]]
    broken: list[dict] = []
    check = internal[:15]
    for link in check:
        try:
            resp = await page.request.head(link["href"], timeout=10000)
            if resp.status >= 400:
                broken.append({"url": link["href"], "text": link["text"], "status": resp.status})
        except Exception:
            broken.append({"url": link["href"], "text": link["text"], "status": 0})

    results.append(TestResult(
        name="No Broken Internal Links", category=TestCategory.BROKEN_LINKS,
        status=TestStatus.FAILED if broken else TestStatus.PASSED,
        message=f"{len(broken)} broken link(s)" if broken
                else f"All {len(check)} internal links OK",
        details={"broken": broken} if broken
                else {"total_links": len(internal), "checked": len(check)},
    ))

    if not links:
        results.append(TestResult(
            name="Page Has Navigation Links", category=TestCategory.BROKEN_LINKS,
            status=TestStatus.WARNING, message="No links found on page",
        ))

    return results


# ---------------------------------------------------------------------------
# 4. BROKEN IMAGES
# ---------------------------------------------------------------------------
async def analyze_images(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1000)
    except Exception:
        return results

    imgs = await page.evaluate("""
        () => [...document.querySelectorAll('img')].map(i => ({
            src: i.src || '', naturalWidth: i.naturalWidth,
            complete: i.complete, hasAlt: i.hasAttribute('alt'),
        }))
    """)

    broken = [i for i in imgs if i["complete"] and i["naturalWidth"] == 0 and i["src"]]
    missing_alt = [i for i in imgs if not i["hasAlt"] and i["src"]]

    results.append(TestResult(
        name="No Broken Images", category=TestCategory.BROKEN_IMAGES,
        status=TestStatus.FAILED if broken else TestStatus.PASSED,
        message=f"{len(broken)} broken image(s)" if broken
                else f"All {len(imgs)} images OK",
        details={"broken": [b["src"][:100] for b in broken[:10]]} if broken
                else {"total_images": len(imgs)},
    ))

    if missing_alt:
        results.append(TestResult(
            name="Images Have Alt Text", category=TestCategory.BROKEN_IMAGES,
            status=TestStatus.WARNING,
            message=f"{len(missing_alt)} image(s) missing alt",
        ))
    elif imgs:
        results.append(TestResult(
            name="Images Have Alt Text", category=TestCategory.BROKEN_IMAGES,
            status=TestStatus.PASSED, message="All images have alt attributes",
        ))

    return results


# ---------------------------------------------------------------------------
# 5. FORMS
# ---------------------------------------------------------------------------
async def analyze_forms(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1500)
    except Exception:
        return results

    # Generic form detection - covers Angular, React, Vue, plain HTML
    info = await page.evaluate("""
        () => {
            const forms = document.querySelectorAll(
                'form, [formGroup], [formgroup], [ngForm], [v-model], [data-form]'
            );
            const inputs = document.querySelectorAll(
                'input:not([type="hidden"]), textarea, select, '
                + 'mat-select, mat-input, [role="combobox"], [role="listbox"]'
            );
            const submits = document.querySelectorAll(
                'button[type="submit"], button:not([type]), input[type="submit"]'
            );
            return {
                formCount: forms.length,
                inputCount: inputs.length,
                submitCount: submits.length,
                inputs: [...inputs].slice(0, 20).map(i => ({
                    tag: i.tagName, type: i.getAttribute('type') || 'text',
                    name: i.getAttribute('name') || i.getAttribute('formcontrolname')
                          || i.getAttribute('v-model') || '',
                    placeholder: i.getAttribute('placeholder') || '',
                    required: i.hasAttribute('required'),
                    disabled: i.disabled,
                    ariaLabel: i.getAttribute('aria-label') || '',
                    id: i.id || '',
                })),
            };
        }
    """)

    if info["formCount"] == 0 and info["inputCount"] == 0:
        results.append(TestResult(
            name="Form Discovery", category=TestCategory.FORMS,
            status=TestStatus.SKIPPED, message="No forms on this page",
        ))
        return results

    results.append(TestResult(
        name="Form Discovery", category=TestCategory.FORMS,
        status=TestStatus.PASSED,
        message=f"{info['formCount']} form(s), {info['inputCount']} input(s), "
                f"{info['submitCount']} submit button(s)",
        details=info,
    ))

    # Label check
    unlabeled = [
        i for i in info["inputs"]
        if i["type"] not in ("hidden", "submit", "button")
        and not (i["ariaLabel"] or i["placeholder"] or i["name"] or i["id"])
    ]
    if unlabeled:
        results.append(TestResult(
            name="Form Inputs Have Labels", category=TestCategory.FORMS,
            status=TestStatus.WARNING,
            message=f"{len(unlabeled)} input(s) lack identifiers",
        ))
    elif info["inputs"]:
        results.append(TestResult(
            name="Form Inputs Have Labels", category=TestCategory.FORMS,
            status=TestStatus.PASSED, message="All inputs identifiable",
        ))

    # Interactability spot-check
    interactable = 0
    for inp in info["inputs"][:5]:
        if inp["disabled"]:
            continue
        sel = f"#{inp['id']}" if inp["id"] else (
            f"[name='{inp['name']}']" if inp["name"] else None
        )
        if sel:
            try:
                if await page.locator(sel).first.is_visible(timeout=2000):
                    interactable += 1
            except Exception:
                pass
    if interactable > 0:
        results.append(TestResult(
            name="Inputs Are Interactable", category=TestCategory.FORMS,
            status=TestStatus.PASSED, message=f"{interactable} input(s) interactable",
        ))

    return results


# ---------------------------------------------------------------------------
# 6. PERFORMANCE
# ---------------------------------------------------------------------------
async def analyze_performance(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []

    start = time.perf_counter()
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        load_ms = (time.perf_counter() - start) * 1000
    except Exception as e:
        return [TestResult(
            name="Page Load Time", category=TestCategory.PERFORMANCE,
            status=TestStatus.FAILED, message=f"Failed: {e}",
        )]

    results.append(TestResult(
        name="Page Load Time", category=TestCategory.PERFORMANCE,
        status=TestStatus.PASSED if load_ms < 3000
               else TestStatus.WARNING if load_ms < 6000
               else TestStatus.FAILED,
        message=f"{load_ms:.0f}ms",
        details={"load_time_ms": round(load_ms)}, duration_ms=load_ms,
    ))

    perf = await page.evaluate("""
        () => {
            const n = performance.getEntriesByType('navigation')[0];
            if (!n) return null;
            return {
                ttfb_ms: Math.round(n.responseStart - n.requestStart),
                dom_interactive_ms: Math.round(n.domInteractive - n.startTime),
                dom_complete_ms: Math.round(n.domComplete - n.startTime),
            };
        }
    """)

    if perf:
        ttfb = perf["ttfb_ms"]
        results.append(TestResult(
            name="Time to First Byte", category=TestCategory.PERFORMANCE,
            status=TestStatus.PASSED if ttfb < 600
                   else TestStatus.WARNING if ttfb < 1500
                   else TestStatus.FAILED,
            message=f"TTFB: {ttfb}ms", details=perf, duration_ms=ttfb,
        ))

        domi = perf["dom_interactive_ms"]
        results.append(TestResult(
            name="DOM Interactive", category=TestCategory.PERFORMANCE,
            status=TestStatus.PASSED if domi < 3000
                   else TestStatus.WARNING if domi < 5000
                   else TestStatus.FAILED,
            message=f"DOM interactive at {domi}ms", duration_ms=domi,
        ))

    res = await page.evaluate("""
        () => {
            const entries = performance.getEntriesByType('resource');
            let total = 0;
            entries.forEach(e => total += e.transferSize || 0);
            return { requests: entries.length, size_kb: Math.round(total / 1024) };
        }
    """)
    if res:
        kb = res["size_kb"]
        results.append(TestResult(
            name="Page Size", category=TestCategory.PERFORMANCE,
            status=TestStatus.PASSED if kb < 2048
                   else TestStatus.WARNING if kb < 5120
                   else TestStatus.FAILED,
            message=f"{kb}KB across {res['requests']} requests",
            details=res,
        ))

    return results


# ---------------------------------------------------------------------------
# 7. ACCESSIBILITY
# ---------------------------------------------------------------------------
async def analyze_accessibility(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1000)
    except Exception:
        return results

    d = await page.evaluate("""
        () => {
            const lang = document.documentElement.getAttribute('lang');
            const h = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')]
                .map(x => parseInt(x.tagName[1]));
            let hierOk = true;
            for (let i = 1; i < h.length; i++) if (h[i] - h[i-1] > 1) hierOk = false;
            const btns = [...document.querySelectorAll('button')];
            const noLabelBtns = btns.filter(b =>
                !b.innerText?.trim() && !b.getAttribute('aria-label') && !b.getAttribute('title')
            ).length;
            const inputs = [...document.querySelectorAll('input:not([type="hidden"])')];
            const noLabelInputs = inputs.filter(i => {
                const id = i.id;
                return !i.getAttribute('aria-label')
                    && !i.getAttribute('aria-labelledby')
                    && !i.getAttribute('placeholder')
                    && !(id && document.querySelector('label[for="'+id+'"]'));
            }).length;
            return {
                hasLang: !!lang, lang: lang || '',
                h1Count: document.querySelectorAll('h1').length,
                hierOk, noLabelBtns, noLabelInputs,
                totalBtns: btns.length, totalInputs: inputs.length,
                viewport: !!document.querySelector('meta[name="viewport"]'),
                landmarks: document.querySelectorAll(
                    'main,[role="main"],nav,[role="navigation"],'
                    + 'header,[role="banner"],footer,[role="contentinfo"]'
                ).length,
            };
        }
    """)

    results.append(TestResult(
        name="HTML lang Attribute", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if d["hasLang"] else TestStatus.FAILED,
        message=f"lang='{d['lang']}'" if d["hasLang"] else "Missing lang attribute",
    ))

    h1 = d["h1Count"]
    results.append(TestResult(
        name="Single H1 Tag", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if h1 == 1
               else TestStatus.WARNING,
        message=f"{h1} H1 heading(s)" if h1 != 1 else "Exactly one H1",
    ))

    results.append(TestResult(
        name="Heading Hierarchy", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if d["hierOk"] else TestStatus.WARNING,
        message="Correct hierarchy" if d["hierOk"] else "Heading levels skip",
    ))

    if d["totalBtns"]:
        results.append(TestResult(
            name="Buttons Accessible", category=TestCategory.ACCESSIBILITY,
            status=TestStatus.FAILED if d["noLabelBtns"] else TestStatus.PASSED,
            message=f"{d['noLabelBtns']} button(s) without names" if d["noLabelBtns"]
                    else f"All {d['totalBtns']} buttons accessible",
        ))

    if d["totalInputs"]:
        results.append(TestResult(
            name="Inputs Have Labels", category=TestCategory.ACCESSIBILITY,
            status=TestStatus.FAILED if d["noLabelInputs"] else TestStatus.PASSED,
            message=f"{d['noLabelInputs']} input(s) unlabeled" if d["noLabelInputs"]
                    else "All inputs labeled",
        ))

    results.append(TestResult(
        name="ARIA Landmarks", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if d["landmarks"] else TestStatus.WARNING,
        message=f"{d['landmarks']} landmark(s)" if d["landmarks"]
                else "No ARIA landmarks found",
    ))

    results.append(TestResult(
        name="Viewport Meta", category=TestCategory.ACCESSIBILITY,
        status=TestStatus.PASSED if d["viewport"] else TestStatus.WARNING,
        message="Present" if d["viewport"] else "Missing viewport meta tag",
    ))

    return results


# ---------------------------------------------------------------------------
# 8. FRAMEWORK HEALTH (auto-adapts to detected framework)
# ---------------------------------------------------------------------------
async def analyze_framework(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    """
    Runs framework-specific health checks based on what was detected.
    Works for Angular, React, Vue, Svelte, Next.js, Nuxt, or falls back to
    generic SPA/MPA checks.
    """
    results: list[TestResult] = []
    fw = discovered.framework

    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
    except Exception:
        return results

    # Report detection
    results.append(TestResult(
        name="Framework Detected", category=TestCategory.FRAMEWORK,
        status=TestStatus.PASSED if fw.name != DetectedFramework.UNKNOWN else TestStatus.WARNING,
        message=f"{fw.name.value}"
                + (f" v{fw.version}" if fw.version else "")
                + (" (SSR)" if fw.is_ssr else "")
                + (" (SPA)" if fw.is_spa and not fw.is_ssr else ""),
        details={"framework": fw.name.value, "version": fw.version,
                 "spa": fw.is_spa, "ssr": fw.is_ssr},
    ))

    # Features
    if fw.features:
        results.append(TestResult(
            name="Libraries & Features", category=TestCategory.FRAMEWORK,
            status=TestStatus.PASSED,
            message=", ".join(fw.features),
            details={"features": fw.features},
        ))

    # ---- Framework-specific checks ----
    health = await page.evaluate("""
        () => {
            const r = {
                appRendered: false,
                rootEmpty: true,
                prodMode: null,
                hydrated: null,
                stateStable: null,
            };

            // ---- ANGULAR ----
            const ngRoot = document.querySelector('app-root') || document.querySelector('[ng-version]');
            if (ngRoot) {
                r.appRendered = true;
                r.rootEmpty = ngRoot.children.length === 0;
                // Zone.js stability
                if (window.getAllAngularTestabilities) {
                    try {
                        r.stateStable = window.getAllAngularTestabilities().every(t => t.isStable());
                    } catch(e) {}
                }
                // Prod mode: ng.getComponent only available in dev mode
                r.prodMode = !(window.ng && window.ng.getComponent);
            }

            // ---- REACT / NEXT / GATSBY ----
            const reactRoot = document.getElementById('root')
                || document.getElementById('__next')
                || document.getElementById('__gatsby');
            if (reactRoot) {
                r.appRendered = true;
                r.rootEmpty = reactRoot.children.length === 0;
                // Check hydration (Next.js / SSR React)
                if (window.__NEXT_DATA__) {
                    r.hydrated = document.querySelector('[data-reactroot]') !== null
                        || reactRoot.children.length > 0;
                }
            }

            // ---- VUE / NUXT ----
            const vueRoot = document.getElementById('app')
                || document.getElementById('__nuxt')
                || document.querySelector('[data-v-app]');
            if (vueRoot && (vueRoot.__vue_app__ || vueRoot.__vue__ || window.__NUXT__)) {
                r.appRendered = true;
                r.rootEmpty = vueRoot.children.length === 0;
                if (window.__NUXT__) {
                    r.hydrated = !document.querySelector('.nuxt-loading');
                }
            }

            // ---- SVELTE ----
            const svelteEls = document.querySelectorAll('[class*="svelte-"]');
            if (svelteEls.length > 0) {
                r.appRendered = true;
                r.rootEmpty = false;
            }

            // ---- GENERIC fallback ----
            if (!r.appRendered) {
                r.appRendered = document.body.children.length > 0
                    && document.body.innerText.trim().length > 20;
                r.rootEmpty = !r.appRendered;
            }

            return r;
        }
    """)

    # App rendered check
    if health.get("appRendered") and not health.get("rootEmpty"):
        results.append(TestResult(
            name="App Rendered", category=TestCategory.FRAMEWORK,
            status=TestStatus.PASSED,
            message="Application root has rendered content",
        ))
    elif health.get("rootEmpty"):
        results.append(TestResult(
            name="App Rendered", category=TestCategory.FRAMEWORK,
            status=TestStatus.FAILED,
            message="App root is empty - may have failed to bootstrap/hydrate",
        ))

    # State stability (Angular Zone.js)
    if health.get("stateStable") is True:
        results.append(TestResult(
            name="State Stable", category=TestCategory.FRAMEWORK,
            status=TestStatus.PASSED,
            message="Framework state is stable (no pending async)",
        ))
    elif health.get("stateStable") is False:
        results.append(TestResult(
            name="State Stable", category=TestCategory.FRAMEWORK,
            status=TestStatus.WARNING,
            message="Framework has pending async operations",
        ))

    # SSR hydration check
    if health.get("hydrated") is True:
        results.append(TestResult(
            name="SSR Hydration", category=TestCategory.FRAMEWORK,
            status=TestStatus.PASSED, message="Page hydrated successfully",
        ))
    elif health.get("hydrated") is False:
        results.append(TestResult(
            name="SSR Hydration", category=TestCategory.FRAMEWORK,
            status=TestStatus.FAILED, message="SSR hydration may have failed",
        ))

    # Production mode
    if health.get("prodMode") is True:
        results.append(TestResult(
            name="Production Mode", category=TestCategory.FRAMEWORK,
            status=TestStatus.PASSED, message="Running in production mode",
        ))
    elif health.get("prodMode") is False:
        results.append(TestResult(
            name="Production Mode", category=TestCategory.FRAMEWORK,
            status=TestStatus.WARNING, message="Running in development mode",
        ))

    return results


# ---------------------------------------------------------------------------
# 9. RESPONSIVE
# ---------------------------------------------------------------------------
async def analyze_responsive(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    viewports = [
        ("Mobile (375x667)", 375, 667),
        ("Tablet (768x1024)", 768, 1024),
        ("Desktop (1920x1080)", 1920, 1080),
    ]

    for label, w, h in viewports:
        try:
            await page.set_viewport_size({"width": w, "height": h})
            await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(1000)

            overflow = await page.evaluate(
                "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            visible = await page.evaluate(
                "() => document.body && document.body.offsetHeight > 0 "
                "&& document.body.innerText.trim().length > 0"
            )

            if not visible:
                st = TestStatus.FAILED
                msg = f"No visible content at {w}x{h}"
            elif overflow:
                st = TestStatus.WARNING
                msg = f"Horizontal overflow at {w}x{h}"
            else:
                st = TestStatus.PASSED
                msg = f"Renders correctly at {w}x{h}"

            results.append(TestResult(
                name=f"Responsive: {label}", category=TestCategory.RESPONSIVE,
                status=st, message=msg,
            ))
        except Exception as e:
            results.append(TestResult(
                name=f"Responsive: {label}", category=TestCategory.RESPONSIVE,
                status=TestStatus.FAILED, message=str(e)[:100],
            ))

    await page.set_viewport_size({"width": 1280, "height": 720})
    return results


# ---------------------------------------------------------------------------
# 10. SEO
# ---------------------------------------------------------------------------
async def analyze_seo(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1000)
    except Exception:
        return results

    seo = await page.evaluate("""
        () => {
            const m = n => (document.querySelector(
                'meta[name="'+n+'"],meta[property="'+n+'"]'
            ) || {}).content || null;
            return {
                title: document.title || '',
                description: m('description'),
                ogTitle: m('og:title'),
                ogDesc: m('og:description'),
                canonical: (document.querySelector('link[rel="canonical"]') || {}).href || null,
                robots: m('robots'),
            };
        }
    """)

    desc = seo.get("description")
    if desc and 50 <= len(desc) <= 160:
        results.append(TestResult(name="Meta Description", category=TestCategory.SEO,
            status=TestStatus.PASSED, message=f"{len(desc)} chars"))
    elif desc:
        results.append(TestResult(name="Meta Description", category=TestCategory.SEO,
            status=TestStatus.WARNING, message=f"Length {len(desc)} - ideal 50-160"))
    else:
        results.append(TestResult(name="Meta Description", category=TestCategory.SEO,
            status=TestStatus.WARNING, message="Missing"))

    title = seo.get("title", "")
    if title and 10 <= len(title) <= 70:
        results.append(TestResult(name="Title Quality", category=TestCategory.SEO,
            status=TestStatus.PASSED, message=f"'{title}' ({len(title)} chars)"))
    elif title:
        results.append(TestResult(name="Title Quality", category=TestCategory.SEO,
            status=TestStatus.WARNING, message=f"Length {len(title)} - ideal 10-70"))

    results.append(TestResult(
        name="Open Graph Tags", category=TestCategory.SEO,
        status=TestStatus.PASSED if seo.get("ogTitle") and seo.get("ogDesc")
               else TestStatus.WARNING,
        message="OG tags present" if seo.get("ogTitle") else "Missing OG tags",
    ))

    if seo.get("canonical"):
        results.append(TestResult(name="Canonical URL", category=TestCategory.SEO,
            status=TestStatus.PASSED, message=seo["canonical"][:80]))

    # Check robots blocking
    robots = seo.get("robots", "")
    if robots and "noindex" in robots.lower():
        results.append(TestResult(name="Robots", category=TestCategory.SEO,
            status=TestStatus.WARNING, message=f"robots: {robots} (noindex blocks crawlers)"))

    return results


# ---------------------------------------------------------------------------
# 11. SECURITY HEADERS
# ---------------------------------------------------------------------------
async def analyze_security_headers(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    try:
        response = await page.goto(discovered.url, wait_until="commit", timeout=30000)
    except Exception:
        return results
    if not response:
        return results

    headers = await response.all_headers()

    checks = [
        ("X-Content-Type-Options", "nosniff", True),
        ("X-Frame-Options", None, True),
        ("Strict-Transport-Security", None, True),
        ("Content-Security-Policy", None, False),
        ("Referrer-Policy", None, False),
        ("Permissions-Policy", None, False),
    ]

    for name, expected, critical in checks:
        val = headers.get(name.lower())
        if val:
            ok = not expected or expected.lower() in val.lower()
            results.append(TestResult(
                name=f"Header: {name}", category=TestCategory.SECURITY_HEADERS,
                status=TestStatus.PASSED if ok else TestStatus.WARNING,
                message=f"{val[:80]}" if ok else f"Unexpected: {val[:60]}",
            ))
        else:
            results.append(TestResult(
                name=f"Header: {name}", category=TestCategory.SECURITY_HEADERS,
                status=TestStatus.WARNING if critical else TestStatus.SKIPPED,
                message=f"Missing {name}",
            ))

    results.append(TestResult(
        name="HTTPS", category=TestCategory.SECURITY_HEADERS,
        status=TestStatus.PASSED if discovered.url.startswith("https://") else TestStatus.FAILED,
        message="HTTPS" if discovered.url.startswith("https://") else "Not HTTPS",
    ))

    return results


# ---------------------------------------------------------------------------
# 12. NETWORK
# ---------------------------------------------------------------------------
async def analyze_network(page: Page, discovered: DiscoveredPage) -> list[TestResult]:
    results: list[TestResult] = []
    failed: list[dict] = []
    all_reqs: list[dict] = []

    def on_resp(resp: Response) -> None:
        entry = {"url": resp.url[:120], "status": resp.status}
        all_reqs.append(entry)
        if resp.status >= 400:
            failed.append(entry)

    page.on("response", on_resp)
    try:
        await page.goto(discovered.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
    except Exception:
        pass
    finally:
        page.remove_listener("response", on_resp)

    NOISE = ["favicon", "analytics", "gtm", "facebook", "hotjar",
             "google-analytics", "doubleclick", "adsense", "clarity"]
    critical = [r for r in failed if not any(n in r["url"].lower() for n in NOISE)]

    results.append(TestResult(
        name="No Failed Requests", category=TestCategory.NETWORK,
        status=TestStatus.FAILED if critical else TestStatus.PASSED,
        message=f"{len(critical)} failed" if critical
                else f"All {len(all_reqs)} requests OK",
        details={"failed": critical[:10]} if critical
                else {"total": len(all_reqs)},
    ))

    api = [r for r in all_reqs if "/api/" in r["url"]]
    bad_api = [r for r in api if r["status"] >= 400]
    if api:
        results.append(TestResult(
            name="API Health", category=TestCategory.NETWORK,
            status=TestStatus.FAILED if bad_api else TestStatus.PASSED,
            message=f"{len(bad_api)}/{len(api)} API calls failed" if bad_api
                    else f"{len(api)} API call(s) OK",
            details={"failed": bad_api[:5]} if bad_api else {},
        ))

    return results


# ---------------------------------------------------------------------------
# ANALYZER REGISTRY
# ---------------------------------------------------------------------------
ALL_ANALYZERS = [
    ("Page Load", analyze_page_load),
    ("Console Errors", analyze_console_errors),
    ("Broken Links", analyze_links),
    ("Broken Images", analyze_images),
    ("Forms", analyze_forms),
    ("Performance", analyze_performance),
    ("Accessibility", analyze_accessibility),
    ("Framework Health", analyze_framework),
    ("Responsive Design", analyze_responsive),
    ("SEO Basics", analyze_seo),
    ("Security Headers", analyze_security_headers),
    ("Network Requests", analyze_network),
]
