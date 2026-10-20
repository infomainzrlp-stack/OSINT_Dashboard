"""Holt alle Daten serverseitig und schreibt sie nach data.json (kein CORS-Problem im Browser)."""
import datetime, email.utils, json, os, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (Lagebild-Dashboard)"}
D, E = {}, []


def get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def J(url, headers=None):
    try:
        D[url] = json.loads(get(url, headers))
    except Exception as e:
        E.append(f"{url[:70]}: {e}")


def N(q, days):
    try:
        u = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": f"{q} when:{days}d", "hl": "de", "gl": "DE", "ceid": "DE:de"})
        out = []
        for it in ET.fromstring(get(u)).iter("item"):
            t = it.findtext("title") or ""
            p = t.rfind(" - ")
            d = email.utils.parsedate_to_datetime(it.findtext("pubDate")).astimezone(datetime.timezone.utc)
            out.append({"t": t[:p] if p > 0 else t, "s": t[p + 3:] if p > 0 else "",
                        "l": it.findtext("link"), "d": d.isoformat()})
        D[f"n:{q}|{days}"] = out[:15]
    except Exception as e:
        E.append(f"News '{q[:40]}': {e}")


J("https://api.open-meteo.com/v1/forecast?latitude=50.11&longitude=8.68&current=temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FBerlin&forecast_days=1")
J("https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/FRANKFURT%20OSTHAFEN/W/currentmeasurement.json")
J("https://api.energy-charts.info/price?bzn=DE-LU")
if os.environ.get("AGSI_KEY"):
    J("https://agsi.gie.eu/api?country=DE&size=30", {"x-key": os.environ["AGSI_KEY"]})
for k in ("064120000000", "073150000000", "064140000000"):
    J(f"https://warnung.bund.de/api31/dashboard/{k}.json")
for la, lo in ((50.11, 8.68), (51.31, 9.48), (50.55, 9.67), (50.58, 8.67), (49.87, 8.65)):
    J(f"https://api.brightsky.dev/alerts?lat={la}&lon={lo}")
for q in ['Polizei Frankfurt Einsatz OR Festnahme OR Unfall OR Großeinsatz -Eintracht -Fußball -Bundesliga', 'site:presseportal.de Polizei Frankfurt', 'Polizeipräsidium Frankfurt Meldung -Eintracht -Fußball', 'Feuerwehr Frankfurt Einsatz OR Brand OR Rettungsdienst -Eintracht -Fußball -Bundesliga', 'Berufsfeuerwehr Frankfurt am Main -Eintracht -Fußball', 'site:presseportal.de Feuerwehr Frankfurt', 'Cyberangriff OR Ransomware OR BSI Warnung Energieversorger OR kritische Infrastruktur', 'Cyberangriff Deutschland', 'Anschlag OR Terror OR Terrorwarnung Deutschland', 'Sabotage OR Spionage Deutschland kritische Infrastruktur']:
    N(q, 2)
for q in ("Stromausfall", "Stromausfall Haushalte Straße",
          "Stromausfall Stadtteil Netzbetreiber", "Stromausfall Gemeinde Störung"):
    N(q, 1)

if not D:
    print("\n".join(E))
    sys.exit(1)
D["_generated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
D["_errors"] = E
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False)
print(f"{len(D) - 2} Quellen ok, {len(E)} Fehler")
for e in E:
    print(" -", e)
