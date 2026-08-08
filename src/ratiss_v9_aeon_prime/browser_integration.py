
# -*- coding: utf-8 -*-
"""
================================================================================
          NAVIGATEUR ET MOTEUR DE BROWSING INTÉGRÉ — RATISS V9
================================================================================
Propriété Intellectuelle : JohnKing0 & Architecte Jonathan Evina
Version du Système       : RATISS V9 AEON PRIME - INTEGRATED QUANTUM ECOSYSTEM
ID ORCID de l'Auteur     : 0009-0000-4092-5313
Ancrage DOI Académique   : 10.17605/OSF.IO/6JZMB
================================================================================

Ce module implémente l'intégration d'un véritable navigateur Chromium managé via
Playwright pour RATISS. Il permet l'exécution dynamique de JavaScript, la
navigation réelle sur Google / Web, la capture d'éléments et la gestion autonome.
================================================================================
"""

import sys
import os
import urllib.request
import json
import asyncio

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class RatissPlaywrightBrowser:
    """
    Navigateur Chromium réel géré par Playwright pour exécuter du JavaScript,
    effectuer des recherches Google en temps réel et extraire le contenu DOM authentique.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 RATISS-AeonPrime/9.0"

    async def browse_url_async(self, url: str) -> dict:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        if not PLAYWRIGHT_AVAILABLE:
            return await self.fallback_urllib_browse(url)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu"
                    ]
                )
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 800},
                    locale="fr-FR"
                )
                page = await context.new_page()

                # Navigation avec attente réseau
                await page.goto(url, wait_until="domcontentloaded", timeout=12000)

                # Si c'est Google Search, tenter de valider les cookies/consentement si présent
                if "google.com" in url or "google.fr" in url:
                    try:
                        # Tenter de cliquer sur le bouton de consentement s'il existe
                        for selector in ["#L2AGLb", "button:has-text('Tout accepter')", "button:has-text('Accept all')", "button:has-text('J\\'accepte')"]:
                            if await page.locator(selector).is_visible():
                                await page.click(selector)
                                await page.wait_for_timeout(1000)
                                break
                    except Exception:
                        pass

                    try:
                        await page.wait_for_selector("div.g, div[data-attrid], #search, h3", timeout=4000)
                    except Exception:
                        pass

                title = await page.title() or "Document sans titre"

                # Extraire tous les paragraphes et textes principaux
                paragraphs = await page.evaluate("""() => {
                    const nodes = Array.from(document.querySelectorAll('h1, h2, h3, p, article, section, div.g, span.st, div.VwiC3b'));
                    return nodes.map(n => n.innerText.trim()).filter(t => t.length > 20);
                }""")

                # Extraire les hyperliens réels
                links = await page.evaluate("""() => {
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    return anchors.map(a => ({
                        text: a.innerText.trim() || a.getAttribute('href'),
                        url: a.href
                    })).filter(l => l.url.startsWith('http') && !l.url.includes('google.com/search') && !l.url.includes('accounts.google') && !l.url.includes('policies.google.com'));
                }""")

                await browser.close()

                # Dédoublonnage des liens
                unique_links = []
                seen_urls = set()
                for l in links:
                    if l['url'] not in seen_urls and len(unique_links) < 20:
                        seen_urls.add(l['url'])
                        unique_links.append(l)

                summary = "\n\n".join(paragraphs[:10]) if paragraphs else "Aucun texte principal extrait."

                return {
                    "status": "success",
                    "engine": "Playwright Managed Chromium",
                    "url": url,
                    "title": title,
                    "text_summary": summary,
                    "total_links_found": len(unique_links),
                    "links": unique_links
                }
        except Exception as e:
            print(f"[PLAYWRIGHT-WARN] Browser execution exception ({e}). Switching to urllib fallback...", file=sys.stderr)
            return await self.fallback_urllib_browse(url)

    async def fallback_urllib_browse(self, url: str) -> dict:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=8) as response:
                html_bytes = response.read()
                html_content = html_bytes.decode("utf-8", errors="ignore")

            title = "Document sans titre"
            paragraphs = []
            links = []

            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, "html.parser")
                if soup.title:
                    title = soup.title.get_text().strip()
                for p in soup.find_all("p"):
                    t = p.get_text().strip()
                    if t:
                        paragraphs.append(t)
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    link_text = a.get_text().strip() or href
                    if href.startswith("http"):
                        links.append({"text": link_text, "url": href})
            else:
                import re
                title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                paragraphs = re.findall(r'<p>(.*?)</p>', html_content, re.DOTALL)[:10]
                paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs]

            return {
                "status": "success",
                "engine": "Urllib Native Fallback",
                "url": url,
                "title": title,
                "text_summary": "\n\n".join(paragraphs[:8]),
                "total_links_found": len(links),
                "links": links[:15]
            }
        except Exception as err:
            return {
                "status": "failed",
                "url": url,
                "error": f"Erreur de navigation : {err}"
            }


def launch_browser(url: str = "http://localhost:3000"):
    browser = RatissPlaywrightBrowser(headless=True)
    res = asyncio.run(browser.browse_url_async(url))
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    launch_browser(target)
