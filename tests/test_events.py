"""events.json, Coming up / Past derivation, .ics, Google Calendar and JSON-LD.

The pure functions in js/events.js run in Node with a frozen clock. The fixture in
tests/fixtures is obviously fake and is never shipped in events.json.
"""
import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


def run_node(data_path, iso_now, expr):
    script = (
        "const E=require(process.argv[1]);const fs=require('fs');"
        "const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));"
        "const now=new Date(process.argv[3]);"
        f"const out=({expr});process.stdout.write(JSON.stringify(out));"
    )
    res = subprocess.run([NODE, "-e", script, str(ROOT / "js" / "events.js"), str(data_path), iso_now],
                         capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(res.stdout)


FIXTURE = ROOT / "tests" / "fixtures" / "events.fixture.json"
SHIPPED = ROOT / "events.json"


@unittest.skipUnless(NODE, "node is required for the events tests")
class EventsTests(unittest.TestCase):
    def test_shipped_events_have_no_upcoming_and_five_past(self):
        for now in ("2026-11-26T12:00:00+11:00", "2030-01-01T00:00:00+11:00"):
            out = run_node(SHIPPED, now, "E.splitEvents(data, now)")
            self.assertEqual(out["upcoming"], [])
            self.assertEqual([e["title"] for e in out["past"]], [
                "Voice of Vineeth Sreenivasan Live", "Talent Show 2K26", "Athletics Day 2026",
                "Onam 2K26", "Onanilavu 2K26"])

    def test_shipped_events_schema(self):
        data = json.loads(SHIPPED.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["timezone"], "Australia/Melbourne")
        ids = [e["id"] for e in data["events"]]
        self.assertEqual(len(ids), len(set(ids)))
        for ev in data["events"]:
            self.assertRegex(ev["id"], r"^[a-z0-9-]+$")
            self.assertIn(ev["category"], {"live", "show", "sport", "onam", "night", "community"})
            self.assertIn(ev["status"], {"upcoming", "past", "cancelled", "postponed"})
            self.assertIn(ev["datePrecision"], {"datetime", "date", "month", "year"})
            if ev["status"] == "upcoming":
                self.assertIn(ev["datePrecision"], {"datetime", "date"}, ev["id"])
                if ev["datePrecision"] == "datetime":
                    self.assertRegex(ev["start"], r"\+1[01]:00$")
                    self.assertTrue(ev["end"], ev["id"])
            for link in ev["links"]:
                self.assertTrue(link["url"].startswith("https://"))

    def test_fixture_upcoming_order_and_display(self):
        out = run_node(FIXTURE, "2027-01-15T12:00:00+11:00",
                       "{s:E.splitEvents(data, now), w:E.splitEvents(data, now).upcoming.map(E.formatWhen),"
                       " ld:E.jsonLd(E.splitEvents(data, now).upcoming)}")
        self.assertEqual([e["id"] for e in out["s"]["upcoming"]],
                         ["test-fixture-daylight-time", "test-fixture-standard-time", "test-fixture-all-day"])
        self.assertEqual(out["w"], ["Saturday, 3 April 2027, 5:30 pm", "Saturday, 10 April 2027, 5:30 pm",
                                    "Saturday, 1 May 2027, All day"])
        self.assertEqual(len(out["ld"]), 3)
        self.assertEqual(out["ld"][0]["@type"], "Event")
        self.assertEqual(out["ld"][0]["startDate"], "2027-04-03T17:30:00+11:00")
        self.assertEqual(out["ld"][0]["location"]["address"]["addressCountry"], "AU")
        self.assertNotIn("location", out["ld"][2])

    def test_fixture_moves_to_past_after_dates(self):
        out = run_node(FIXTURE, "2027-06-15T12:00:00+10:00", "E.splitEvents(data, now)")
        self.assertEqual(out["upcoming"], [])
        self.assertEqual(len(out["past"]), 3)

    def test_ics_across_daylight_saving(self):
        out = run_node(FIXTURE, "2027-01-15T12:00:00+11:00",
                       "data.events.map(e => E.buildIcs(e, now))")
        first, second, allday = out
        self.assertIn("DTSTART:20270403T063000Z\r\n", first)
        self.assertIn("DTEND:20270403T103000Z\r\n", first)
        self.assertIn("UID:test-fixture-daylight-time@shema.com.au\r\n", first)
        self.assertIn("DTSTAMP:20270115T010000Z\r\n", first)
        unfolded = first.replace("\r\n ", "")
        self.assertIn(r"Fixture text\; commas\, semicolons and a backslash \\ test escaping.", unfolded)
        self.assertIn("LOCATION:Example Hall (test fixture)\\, 1 Example Street\\, Testville VIC 0000", unfolded)
        self.assertIn("DTSTART:20270410T073000Z\r\n", second)
        self.assertIn("DTEND:20270410T113000Z\r\n", second)
        self.assertIn("DTSTART;VALUE=DATE:20270501\r\n", allday)
        self.assertIn("DTEND;VALUE=DATE:20270502\r\n", allday)
        self.assertNotIn("LOCATION", allday)
        for ics in out:
            self.assertTrue(ics.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"))
            self.assertTrue(ics.endswith("END:VEVENT\r\nEND:VCALENDAR\r\n"))
            for line in ics.split("\r\n"):
                self.assertLessEqual(len(line.encode("utf-8")), 75, line)

    def test_google_calendar_link(self):
        out = run_node(FIXTURE, "2027-01-15T12:00:00+11:00", "data.events.map(E.googleLink)")
        self.assertIn("dates=20270403T063000Z%2F20270403T103000Z", out[0])
        self.assertIn("ctz=Australia%2FMelbourne", out[0])
        self.assertTrue(out[0].startswith("https://calendar.google.com/calendar/render?action=TEMPLATE&text="))
        self.assertIn("dates=20270501%2F20270502", out[2])

    def test_no_fixture_text_shipped(self):
        for path in ROOT.rglob("*"):
            if not path.is_file() or "tests" in path.parts or ".git" in path.parts or "tools" in path.parts:
                continue
            if path.suffix not in {".html", ".js", ".json", ".css", ".xml", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("TEST FIXTURE", text, path)
            self.assertNotIn("example.com", text, path)


class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self._card = None
        self._field = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and a.get("class") == "event-card event-memory-card reveal":
            self._card = {"title": "", "desc": "", "links": []}
            self.cards.append(self._card)
        elif self._card is not None:
            if tag == "h3":
                self._field = "title"
            elif tag == "p" and "event-desc" in (a.get("class") or ""):
                self._field = "desc"
            elif tag == "a":
                self._card["links"].append([a.get("href"), ""])
                self._field = "link"

    def handle_endtag(self, tag):
        if tag in ("h3", "p", "a"):
            self._field = None
        if tag == "article":
            self._card = None

    def handle_data(self, data):
        if self._card is None or not self._field:
            return
        if self._field == "link":
            self._card["links"][-1][1] += data
        else:
            self._card[self._field] += data


class DriftTests(unittest.TestCase):
    def test_static_past_cards_match_events_json(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        parser = Cards()
        parser.feed(html)
        data = json.loads(SHIPPED.read_text(encoding="utf-8"))
        expected = [{"title": e["title"], "desc": e["description"],
                     "links": [[l["url"], l["label"]] for l in e["links"]]}
                    for e in data["events"] if e["status"] == "past"]
        got = [{"title": c["title"].strip(), "desc": re.sub(r"\s+", " ", c["desc"]).strip(),
                "links": [[h, re.sub(r"\s+", " ", t).strip()] for h, t in c["links"]]} for c in parser.cards]
        self.assertEqual(got, expected)

    def test_honest_card_is_static_default(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        upcoming = html.split('id="upcomingList"', 1)[1].split("</div>\n      </div>", 1)[0]
        self.assertIn("Next event to be announced", upcoming)
        self.assertIn("https://www.facebook.com/sheppartonmc", upcoming)


if __name__ == "__main__":
    unittest.main()
