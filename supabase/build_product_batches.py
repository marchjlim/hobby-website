import concurrent.futures
import csv
import glob
import html
import json
import re
import ssl
import time
import unicodedata
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "supabase"
START_BATCH = 3
HEADERS = [
    "canonical_name",
    "grade",
    "scale",
    "msrp",
    "msrp_currency",
    "original_release_date",
    "last_reproduction_date",
]
MANUAL_CATEGORIES = {"1": "HG", "5": "HG", "6": "MG", "9": "PG", "10": "RG", "4": "MG"}
GLOBAL_BRANDS = ("hg", "mg", "mgka", "rg", "pg", "fullmechanics")
MANUAL = "https://manual.bandai-hobby.net/"
GLOBAL = "https://global.bandai-hobby.net/en-us/"
GUNDAM_BASE_SUPPLEMENTS = (
    ("HG 1/144 ZETA GUNDAM [CLEAR COLOR]", "HG", "1/144", "2017-11-01"),
    ("HG 1/144 GUNDAM BARBATOS LUPUS REX[IRON-BLOODED COATING]", "HG", "1/144", "2020-06-06"),
    ("HG 1/144 GM SPARTAN", "HG", "1/144", "2022-12-01"),
    ("HG 1/144 PALE RIDER DII (TITANS)", "HG", "1/144", "2021-08-01"),
    ("HG 1/144 MOON GUNDAM [CLEAR COLOR]", "HG", "1/144", "2019-10-12"),
    ("HG 1/144 GUNDAM TR-6 [WONDWORT]", "HG", "1/144", "2018-06-01"),
    ("HG 1/144 EFREET NACHT", "HG", "1/144", "2018-04-01"),
    ("HG 1/144 GM SNIPER", "HG", "1/144", "2017-07-01"),
    ("MG 1/100 MSZ-006P2/3C ZETA GUNDAM III P2 TYPE RED ZETA", "MG", "1/100", "2015-06-01"),
    ("MG 1/100 MSZ-006-3B ZETA GUNDAM 3B TYPE GRAY ZETA", "MG", "1/100", "2015-02-01"),
)
DUPLICATE_ALIASES = {
    "HG 1/144 CROSS BONE GUNDAM MAOU",
    "HG 1/144 Ankusha",
    "HG 1/144 Dauben Wolf",
    "HG 1/144 Dauben Wolf (Unicorn Ver.)",
    "HG 1/144 GELGOOG J",
    "HG 1/144 GUNDAM Fenice Rina Cita",
    "HG 1/144 GUNDAM X Demon King",
    "HG 1/144 GUNDAM Gusion Rebaking City",
    "HG 1/144 GUNDAM TR-6 [WONDWART]",
    "HG 1/144 HI-GOGG",
    "HG 1/144 EXIA",
    "HG 1/144 PMX-002 BOLINOAK-SAMMAHN",
    "HG 1/144 PORTENT FLYER",
    "HG 1/144 GAIA'S RICK DOM/ORTEGA’S RICK DOM(GQ)",
    "MG 1/100 GUNDAM ASTRAY BLUE FLAME D",
    "MG 1/100 GUNDAM AVALANCHE EXIA’",
    "MG 1/100 GUNDAM ASTRAY TURN RED",
    "MG 1/100 GUNDAM BASS LIMITED ZAKUWARRIOR (LIVE CONCERT VER.)",
    "MG 1/100 GUNDAM BASE LIMITED V2 ASSAULT BUSTER GUNDAM VER.KA [TITANIUM FINISH]",
    "MG 1/100 GM COMMAND (COLONY TYPE)",
    "MG 1/100 GUNDAM F91 ver2.0 BACK CANNON TYPE & TWIN V.S.B.R. SET UP TYPE",
    "MG 1/100 NEW GUNDAM Ver. Ka",
    "MG 1/100 PHILIP HUGHS’S GM DOMINANCE",
    "PG 1/60 MS-06S ZAKUII",
    "PG 1/60 GP01 RX-78 GUNDAM GP01/FB",
    "PG 1/60 OO-RAISER",
    "PG 1/60 RX-178 GUNDAM MK-IIA.E.U.G (WHITE)",
    "PG 1/60 RX-178 GUNDAM MK-IITITANS (BLACK)",
    "PG 1/60 UNICORN GUNDAM 03 PHENEX",
    "PG 1/60 W-GUNDAM ZERO CUSTOM",
    "PG 1/60 SKY GRASPER",
    "PG 1/60 Z GUNDAM",
    "RG 1/144 GN-0000+GNR-010 Double O Riser",
    "RG 1/144 GN-0000+GNR-010 OO RAISER",
    "RG 1/144 GUNDAM Base Limited Sinanju [Metallic Gloss Injection]",
    "RG 1/144 GUNDAM BASE LIMITED ZGMF-X10A FREEDOM GUNDAM VER.GCP",
    "RG 1/144 MSM-07S Char Exclusive Zugok",
    "RG 1/144 MS-06S ZAKUII",
    "RG 1/144 OO QAN[T]",
    "RG 1/144 ν GUNDAM DOUBLE FIN FUNNEL TYPE",
}
USER_AGENT = {"User-Agent": "Mozilla/5.0 (compatible; GundamCatalogResearch/1.0)"}
SSL_CONTEXT = ssl.create_default_context()


def fetch(url, headers=None):
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers=headers or USER_AGENT)
            with urllib.request.urlopen(request, context=SSL_CONTEXT, timeout=40) as response:
                return response.read().decode("utf-8", "replace")
        except Exception:
            if attempt == 3:
                raise
            time.sleep(0.5 * 2**attempt)


def clean(value):
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def semantic_key(name):
    value = unicodedata.normalize("NFKC", name).upper()
    value = value.replace("Ν", "NU").replace("ν", "NU").replace("∀", "TURN A")
    value = re.sub(r"\(GUNDAM THE ORIGIN\s*(?:VER\.?)?\)", "(THE ORIGIN)", value)
    return re.sub(r"[^A-Z0-9]+", "", value)


def canonicalize(name, source):
    name = clean(name)
    full_mechanics = source in {"4", "fullmechanics"}
    if full_mechanics:
        match = re.match(r"^(?:FULL MECHANICS\s+)?(\d+/\d+)\s+(?:FULL MECHANICS\s+)?(.+)$", name, re.I)
        if not match:
            return None
        scale, product = match.groups()
        if product.upper().endswith("(FULL MECHANICS)"):
            product = product[: -len("(FULL MECHANICS)")].rstrip()
        return f"MG {scale} {product} (FULL MECHANICS)", "MG", scale

    unleashed = re.match(r"^PG\s+UNLEASHED\s+(\d+/\d+)\s+(.+)$", name, re.I)
    if unleashed:
        scale, product = unleashed.groups()
        return f"PG {scale} {product} (PG UNLEASHED)", "PG", scale

    match = re.match(r"^(HG[A-Z0-9-]*|MG|RG|PG)\s+(\d+/\d+)\s+(.+)$", name, re.I)
    if not match:
        return None
    raw_grade, scale, product = match.groups()
    grade = "HG" if raw_grade.upper().startswith("HG") else raw_grade.upper()
    if grade == "MG" and scale == "1/00":
        scale = "1/100"  # Official English entry typo; Japanese product title says 1/100.
    return f"{grade} {scale} {product}", grade, scale


def is_complete_kit(name):
    product = re.sub(r"^(?:HG|MG|RG|PG)\s+\d+/\d+\s+", "", name, flags=re.I)
    blocked = (
        r"^EXPANSION\b",
        r"^OPTION (?:PARTS|SET)\b",
        r"^MISSION PACK\b",
        r"^WEAPONS? SET\b",
        r"^PARTS SET\b",
        r"^B-PACKS EXPANSION\b",
        r"^LED UNIT\b",
        r"^LIGHTING UNIT\b",
        r"^EFFECT PARTS\b",
        r"^ACTION BASE\b",
        r"^ASSAULT BOOSTER & HIGH MOBILITY UNIT\b",
        r"^ASSAULT BUSTER EXPANSION PARTS\b",
        r"^GUNDAM DECAL\b",
        r"^HYPER MEGA BAZOOKA LAUNCHER\b",
        r"^DOUBLE FIN FUNNEL\b",
        r"^MIRASOUL FLIGHT UNIT\b",
        r"^METEOR UNIT$",
        r"^CLEAR COLOR BODY\b",
        r"^24TH CENTURY WEAPONS\b",
        r"^AMAGING WEAPON BINDER\b",
        r"^AMAZING BOOSTER\b",
        r"^AVALANCHE.+UNIT FOR\b",
        r"^BALLISTIC WEAPONS\b",
        r"^BALLUTE PACK\b",
        r"^BOOSTER BED FOR\b",
        r"^BUILD BOOSTER\b",
        r"^BUILD HANDS\b",
        r"^CUSTOM SET\b",
        r"^DARK MATTER BOOSTER\b",
        r"^DESTINY GUNDAM EFFECT UNIT\b",
        r"^DIVER ACE UNIT\b",
        r"^DRAGOON (?:DISPLAY EFFECT|FORMATION BASE)\b",
        r"^ENHANCED EXPANSION PARTS\b",
        r"^FIN FUNNEL EFFECT\b",
        r"^FULL ARMOR EXPANSION EFFECT UNIT\b",
        r"^G-PARTS\b",
        r"^GALAXY BOOSTER\b",
        r"^GM GM WEAPONS\b",
        r"^GUNDAM BASE LIMITED MS CAGE\b",
        r"^GUNDAM G-SELF OPTION UNIT\b",
        r"^GUNNER WIZARD/.+ SET\b",
        r"^GYA EASTERN WEAPONS\b",
        r"^HEAVY GROUND ARMOR UNIT EXPANSION PARTS\b",
        r"^HWS & SV CUSTOM WEAPON SET\b",
        r"^HYPER GUNPLA BATTLE WEAPONS\b",
        r"^INJUSTICE WEAPONS\b",
        r"^K9 DOG PACK\b",
        r"^KURENAI WEAPON\b",
        r"^LIGHTNING BACK WEAPON SYSTEM\b",
        r"^(?:LIGHTNING|MANEUVER|RAIJIN) STRIKER\b.+\bFOR\b",
        r"^MARSFOUR WEAPONS\b",
        r"^MATSURI WEAPON\b",
        r"^NU GUNDAM VER\.KA DOUBLE FIN FUNNEL CUSTOM UNIT\b",
        r"^NINPULSE BEAMS\b",
        r"^PERFECT STRIKE GUNDAM EXPANSION PARTS\b",
        r"^QUBELEY FUNNEL EFFECT SET\b",
        r"^SHIRANUI UNIT FOR\b",
        r"^SKULL WEAPON\b",
        r"^TILTROTOR PACK\b",
        r"^UNIVERSE BOOSTER\b",
        r"^VEETWO WEAPONS\b",
        r"^V2 GUNDAM EFFECT UNIT\b",
        r"^WEAPON & ARMOR HANGER\b",
        r"\bMISSION PACK\b",
        r"\bEXPANSION (?:PARTS )?SET\b",
        r"\bOPTION SET\b",
    )
    return not any(re.search(pattern, product, re.I) for pattern in blocked)


def manual_date(value):
    match = re.search(r"(\d{4})年(?:(\d+)月)?(?:(\d+)日)?発売", value)
    if not match or not match.group(2):
        return ""
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day or 1):02d}"


def global_date(value):
    months = {name: number for number, name in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
    exact = re.search(r"(\d{1,2})\s+([A-Z][a-z]{2})\.\s+(\d{4})", value)
    if exact:
        day, month, year = exact.groups()
        return f"{year}-{months[month]:02d}-{int(day):02d}"
    partial = re.search(r"([A-Z][a-z]{2})\.\s+(\d{4})", value)
    if partial:
        month, year = partial.groups()
        return f"{year}-{months[month]:02d}-01"
    return ""


def existing_names():
    names = set()
    for number in range(1, START_BATCH):
        with (OUT / f"products_batch_{number}.csv").open(encoding="utf-8-sig", newline="") as source:
            names.update(row["canonical_name"] for row in csv.DictReader(source))

    client = (ROOT / "src" / "supabase-client.ts").read_text(encoding="utf-8")
    project_url = re.search(r"https://[a-z0-9-]+\.supabase\.co", client).group(0)
    anon_key = re.search(r"eyJ[A-Za-z0-9._-]+", client).group(0)
    start = 0
    while True:
        headers = {**USER_AGENT, "apikey": anon_key, "Authorization": f"Bearer {anon_key}", "Range": f"{start}-{start + 999}"}
        rows = json.loads(fetch(f"{project_url}/rest/v1/products?select=canonical_name&order=id.asc", headers))
        names.update(row["canonical_name"] for row in rows)
        if len(rows) < 1000:
            break
        start += 1000
    return names


def gundam_title_ids(index):
    ids = set()
    pattern = r'name="titles\[\]" value="(\d+)".*?<label[^>]*>.*?alt="([^"]+)"'
    for title_id, label in re.findall(pattern, index, re.S):
        if re.search(r"ガンダム|GUNDAM|ADVANCE OF Z|その他ガンプラ", html.unescape(label), re.I):
            ids.add(title_id)
    return ids


def manual_pages():
    pages = {}
    requests = []
    for category in MANUAL_CATEGORIES:
        first = fetch(f"{MANUAL}?categories%5B0%5D={category}")
        pages[(category, 1)] = first
        count = int(re.search(r"([\d,]+)件の結果", first).group(1).replace(",", ""))
        requests.extend((category, page) for page in range(2, (count + 19) // 20 + 1))

    def load(item):
        category, page = item
        return category, page, fetch(f"{MANUAL}?categories%5B0%5D={category}&page={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for category, page, body in executor.map(load, requests):
            pages[(category, page)] = body
    return pages


def manual_records(title_ids):
    records = []
    for (category, _), body in manual_pages().items():
        for item in body.split('<div class="bl_result_item">')[1:]:
            title = re.search(r"/images/titles/(\d+)\.jpeg", item)
            english = re.search(r'<span class="bl_result_name_en">(.*?)</span>', item, re.S)
            if not title or title.group(1) not in title_ids or not english:
                continue
            parsed = canonicalize(english.group(1), category)
            if not parsed or not is_complete_kit(parsed[0]):
                continue
            date = re.search(r"<dd>(\d{4}年(?:\d+月)?(?:\d+日)?発売)</dd>", item)
            records.append((*parsed, manual_date(date.group(1)) if date else ""))
    return records


def global_records(known_keys):
    pages = {}
    requests = []
    for brand in GLOBAL_BRANDS:
        first = fetch(f"{GLOBAL}brand/{brand}/")
        pages[(brand, 1)] = first
        page_count = max((int(page) for page in re.findall(r'href="\./\?p=(\d+)"', first)), default=1)
        requests.extend((brand, page) for page in range(2, page_count + 1))

    def load_page(item):
        brand, page = item
        return brand, page, fetch(f"{GLOBAL}brand/{brand}/?p={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for brand, page, body in executor.map(load_page, requests):
            pages[(brand, page)] = body

    candidates = {}
    card_pattern = r'<a href="https://global\.bandai-hobby\.net/en-us/item/([^/]+)/" class="c-card p-card -landscape">(.*?)</a>'
    for (brand, _), body in pages.items():
        for item_id, card in re.findall(card_pattern, body, re.S):
            title = re.search(r'<div class="p-card__tit">(.*?)</div>', card, re.S)
            date = re.search(r'<div class="p-card_date">(.*?)</div>', card, re.S)
            if not title:
                continue
            parsed = canonicalize(title.group(1), brand)
            if not parsed or not is_complete_kit(parsed[0]) or semantic_key(parsed[0]) in known_keys:
                continue
            candidates[item_id] = (*parsed, global_date(clean(date.group(1))) if date else "")

    index = fetch(f"{GLOBAL}item_all/")
    gundam_slugs = {
        slug
        for slug, label in re.findall(r'name="series"[^>]*value="([^"]+)"[^>]*><label[^>]*>(.*?)</label>', index, re.S)
        if re.search(r"gundam|gunpla", clean(label), re.I)
    }

    def classify(item_id):
        body = fetch(f"{GLOBAL}item/{item_id}/")
        return item_id, set(re.findall(r"/series/([^/]+)/", body))

    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for item_id, slugs in executor.map(classify, candidates):
            if slugs & gundam_slugs:
                records.append(candidates[item_id])
    return records


def dedupe(records, excluded):
    excluded_keys = {semantic_key(name) for name in excluded}
    unique = {}
    for canonical_name, grade, scale, release_date in records:
        if canonical_name in DUPLICATE_ALIASES:
            continue
        key = semantic_key(canonical_name)
        if key in excluded_keys:
            continue
        row = {
            "canonical_name": canonical_name,
            "grade": grade,
            "scale": scale,
            "msrp": "",
            "msrp_currency": "JPY",
            "original_release_date": release_date,
            "last_reproduction_date": "",
        }
        previous = unique.get(key)
        if not previous or (release_date and (not previous["original_release_date"] or release_date < previous["original_release_date"])):
            unique[key] = row
    return list(unique.values())


def balanced(rows):
    groups = {grade: sorted((row for row in rows if row["grade"] == grade), key=lambda row: row["canonical_name"].casefold()) for grade in ("HG", "MG", "RG", "PG")}
    result = []
    while any(groups.values()):
        for grade in ("HG", "MG", "RG", "PG"):
            if groups[grade]:
                result.append(groups[grade].pop(0))
    return result


def validate(rows, excluded):
    excluded_keys = {semantic_key(name) for name in excluded}
    keys = [semantic_key(row["canonical_name"]) for row in rows]
    assert len(keys) == len(set(keys))
    assert not set(keys) & excluded_keys
    for row in rows:
        assert row["grade"] in {"HG", "MG", "RG", "PG"}
        assert row["canonical_name"].startswith(f'{row["grade"]} {row["scale"]} ')
        assert not row["msrp"] or re.fullmatch(r"\d+(?:\.\d+)?", row["msrp"])
        for field in ("original_release_date", "last_reproduction_date"):
            assert not row[field] or re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[field])


def main():
    collisions = glob.glob(str(OUT / "products_batch_[3-9]*.csv"))
    if collisions:
        raise SystemExit(f"Refusing to overwrite existing generated batches: {collisions}")
    excluded = existing_names()
    index = fetch(MANUAL)
    manual = manual_records(gundam_title_ids(index))
    known = {semantic_key(record[0]) for record in manual} | {semantic_key(name) for name in excluded}
    rows = dedupe(manual + global_records(known) + list(GUNDAM_BASE_SUPPLEMENTS), excluded)
    rows = balanced(rows)
    validate(rows, excluded)

    for offset in range(0, len(rows), 100):
        number = START_BATCH + offset // 100
        with (OUT / f"products_batch_{number}.csv").open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=HEADERS, lineterminator="\r\n")
            writer.writeheader()
            writer.writerows(rows[offset : offset + 100])

    counts = {grade: sum(row["grade"] == grade for row in rows) for grade in ("HG", "MG", "RG", "PG")}
    print(f"created={len(rows)} batches={(len(rows) + 99) // 100} excluded_existing={len(excluded)} grades={counts}")


if __name__ == "__main__":
    main()
