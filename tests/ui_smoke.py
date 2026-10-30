#!/usr/bin/env python3
import json, os, re, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "editions.json").read_text())
EXPECTED_TITLES = {
    "2026-08-21": ["Politischer Klamauk", "Alle Wege führen nach Olten", "Gartenstühle des Grauens", "Trumpscher Coup auf Schweizer Art", "Mit Daten gegen überrissene Mieten", "Schwangerschaftsabbruch schwer gemacht"],
    "2026-08-14": ["Finde deine Grosseltern", "Aus dem Land gewürfelt", "Sie riskieren ihr Leben", "Wenn die Hitze auf die Psyche schlägt", "Dünnsein ist ansteckend"],
    "2026-08-07": ["Zwei Fäuste gegen Femizide", "Stadt, Land, Hölle", "Angriff der Sozialistinnen", "Die Macht des Privatrechts", "Musik hören ist antikapitalistisch", "Ausdauernd wie ein Flamingo"],
    "2026-07-31": ["Kontrolle ist gut, Vertrauen ist besser", "Willkommen in der Medienvielfaltswoche", "Ausgebeutet im Nobelrestaurant", "Meine Meinung!", "Geflüchtete Teenager reisen nach Auschwitz", "Getragen durch die Gruppe"],
    "2026-07-24": ["Reise ins Wunderland", "Ein Medienminister auf Mission", "Gigantische Zukunft", "Wasserknappheit im Wilden Westen", "Was Trumps Zölle bisher bewirkten", "Madre mia!"],
    "2026-07-17": ["Klartext aus der Fussballkabine", "Chinas stille Revolution", "Mensch gegen Maschine", "Schaut auf die Haut!"],
}
EXPECTED_TITLES = json.loads((ROOT / 'tests/expected_titles.json').read_text())
assert manifest["latest"] == "2026-10-30"
assert manifest['editions'][0]['status'] == 'complete'
assert manifest['editions'][0]['sourceCount'] == 6
assert manifest['editions'][0]['asOf'].startswith('2026-10-30T')
assert manifest['editions'][1]['status'] == 'complete'
assert manifest['editions'][1]['sourceCount'] == 6
assert [e["end"] for e in manifest["editions"]] == list(EXPECTED_TITLES)
assert all(e["count"] == len(EXPECTED_TITLES[e["end"]]) for e in manifest["editions"])
assert sum(e["count"] for e in manifest["editions"]) == 93

paths = [("", manifest['latest'])] + [(e["href"], e["end"]) for e in manifest["editions"]]
# Root and the latest archive intentionally render the same edition.
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

server = None
base_url = os.environ.get('BASE_URL')
if not base_url:
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        errors = []
        for path, edition in paths:
            for width, height in ((1440, 950), (390, 844)):
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("console", lambda msg, path=path: errors.append(f"{path}: {msg.text}") if msg.type == "error" else None)
                page.on("pageerror", lambda exc, path=path: errors.append(f"{path}: {exc}"))
                response = page.goto(base_url.rstrip('/') + '/' + path, wait_until="networkidle")
                assert response is not None and response.status == 200, path
                page.wait_for_function("() => document.documentElement.dataset.ready === 'true'")
                cards = page.locator(".item-card")
                expected = EXPECTED_TITLES[edition]
                assert cards.count() == len(expected), (path, cards.count(), len(expected))
                assert page.locator(".edition-inner a,.edition-inner span").count() == len(EXPECTED_TITLES)
                assert page.locator(".open-link").count() == len(expected)
                assert page.locator(".duration").count() == len(expected)
                assert page.locator("h3").all_text_contents() == expected
                hrefs = page.locator(".open-link").evaluate_all("nodes => nodes.map(n => n.href)")
                for card, href in zip(cards.all(), hrefs):
                    url = urlsplit(href)
                    allowed_hosts = {"www.republik.ch", "www.atmo-magazin.de", "www.dossier.at", "54books.de", "reportagen.com", "krautreporter.de"}
                    assert url.scheme == "https" and url.hostname in allowed_hosts
                    assert not url.query and not url.fragment and not url.username and not url.password
                    text = card.inner_text()
                    display_host = (url.hostname or "").removeprefix("www.")
                    assert display_host in text and (re.search(r"≈ \d+ Min\. Lesezeit", text) or "Lesezeit nicht angegeben" in text)
                body = page.locator("body").inner_text()
                if edition == '2026-10-30':
                    assert 'Zwischenstand' not in body and 'Redaktionsschluss:' in body
                    assert '6 Newsletter vom 24. bis 30. Oktober' in body
                if edition in ('2026-10-23', '2026-10-30'):
                    assert page.locator('.source-note').count() == len(expected)
                    assert all('Auf Grundlage des Newsletters' in s for s in page.locator('.source-note').all_text_contents())
                    assert page.locator('.item-card[id^="beitrag-"]').count() == len(expected)
                    assert 'Lesezeit nicht angegeben' in body
                assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", body)
                assert not any(secret in body for secret in ("/home/", "messageId", "Label_", "icloud.com", "Guten Morgen "))
                assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
                for button in page.locator('[data-filter]').all():
                    kind = button.get_attribute('data-filter')
                    button.click()
                    expected_visible = len(expected) if kind == 'all' else page.locator(f'.item-card[data-type="{kind}"]').count()
                    assert page.locator('.item-card:visible').count() == expected_visible
                    assert button.get_attribute('aria-pressed') == 'true'
                    assert page.locator('#result-count').inner_text().startswith(str(expected_visible) + ' ')
                page.locator('[data-filter="all"]').click()
                for tab in page.locator('.edition-inner a').all():
                    href = tab.get_attribute('href')
                    assert href is not None
                    destination = urlsplit(href).path
                    assert (ROOT / path / destination / 'index.html').resolve().is_file()
                # Exercise real navigation, not just local path existence.
                tab = page.locator('.edition-inner a').first
                target_edition = tab.inner_text().split(' · ')[0]
                tab.click()
                page.wait_for_load_state('networkidle')
                page.wait_for_function("() => document.documentElement.dataset.ready === 'true'")
                assert page.locator('h3').all_text_contents() == EXPECTED_TITLES[target_edition]
                page.go_back(wait_until='networkidle')
                page.wait_for_function("() => document.documentElement.dataset.ready === 'true'")
                assert page.locator('h3').all_text_contents() == expected
                if path == "" and width == 1440:
                    page.screenshot(path=str(ROOT / "test-results-desktop.png"), full_page=True)
                if path == "" and width == 390:
                    page.screenshot(path=str(ROOT / "test-results-mobile.png"), full_page=True)
                page.close()
        browser.close()
        assert not errors, errors
    print(f"Republik UI smoke passed: {len(manifest['editions'])} editions, {sum(e['count'] for e in manifest['editions'])} cards, clean direct links, hostname/duration visibility, editorial cutoff, privacy, console, desktop/mobile overflow and navigation")
finally:
    if server:
        server.shutdown()
        server.server_close()
