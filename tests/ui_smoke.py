#!/usr/bin/env python3
import json, re, subprocess, sys, time
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
assert manifest["latest"] == "2026-09-18"
assert [e["end"] for e in manifest["editions"]] == list(EXPECTED_TITLES)
assert all(e["count"] == len(EXPECTED_TITLES[e["end"]]) for e in manifest["editions"])
assert sum(e["count"] for e in manifest["editions"]) == 56

paths = [("", manifest['latest'])] + [(e["href"], e["end"]) for e in manifest["editions"]]
# Root and the latest archive intentionally render the same edition.
server = subprocess.Popen([sys.executable, "-m", "http.server", "8766"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        errors = []
        for path, edition in paths:
            for width, height in ((1440, 950), (390, 844)):
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("console", lambda msg, path=path: errors.append(f"{path}: {msg.text}") if msg.type == "error" else None)
                page.on("pageerror", lambda exc, path=path: errors.append(f"{path}: {exc}"))
                page.goto("http://127.0.0.1:8766/" + path, wait_until="networkidle")
                page.wait_for_function("document.documentElement.dataset.ready === 'true'")
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
                    assert display_host in text and re.search(r"≈ \d+ Min\. Lesezeit", text)
                body = page.locator("body").inner_text()
                assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", body)
                assert not any(secret in body for secret in ("/home/", "messageId", "Label_", "icloud.com", "Guten Morgen Armin"))
                assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
                if path == "" and width == 1440:
                    page.screenshot(path=str(ROOT / "test-results-desktop.png"), full_page=True)
                if path == "" and width == 390:
                    page.screenshot(path=str(ROOT / "test-results-mobile.png"), full_page=True)
                page.close()
        browser.close()
        assert not errors, errors
    print("Republik UI smoke passed: 10 editions, 56 cards, clean direct links, hostname/duration visibility, privacy, console, desktop/mobile overflow")
finally:
    server.terminate()
    server.wait(timeout=5)
