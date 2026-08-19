import concurrent.futures
import csv
import glob
import html
import math
import re
import sys
import time
import unicodedata
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

from build_product_batches import GLOBAL, GLOBAL_BRANDS, HEADERS, MANUAL, MANUAL_CATEGORIES, OUT, canonicalize, clean


UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"}
HANGAR = "https://gunplahangar.com/kits"
PREMIUM = "https://pbcharacterplastic.bandai-hobby.net/catalog"
GUNDAM_BASE = "https://www.gundam-base.net/products/index.php"
GUNPLA_IN = "https://gunpla.in/search/gunpla/grade"
VARIANTS = (
    "CLEAR COLOR",
    "TITANIUM FINISH",
    "SPECIAL COATING",
    "IRON BLOODED COATING",
    "EXTRA FINISH",
    "GUNDAM BASE",
    "EVENT LIMITED",
    "METALLIC",
    "ECOPLA",
    "TRANS AM",
    "PG UNLEASHED",
    "FULL MECHANICS",
)
FUZZY_EXCEPTIONS = {
    "HG 1/144 GUNDAM X D.V.",
    "HG 1/144 O GUNDAM",
    "RG 1/144 CROSSBONE GUNDAM X2",
    "RG 1/144 GUNDAM ASTRAY BLUE FRAME",
}


def fetch(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as response:
                return response.read().decode("utf-8", "replace")
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2**attempt)


def key(value):
    value = unicodedata.normalize("NFKC", value).upper().replace("Ν", "NU").replace("∀", "TURN A")
    value = re.sub(r"\(GUNDAM THE ORIGIN\s*(?:VER\.?)?\)", "(THE ORIGIN)", value)
    value = value.replace("THE GUNDAM BASE LIMITED", "GUNDAM BASE LIMITED")
    return re.sub(r"[^A-Z0-9]+", "", value)


def parts(canonical_name):
    match = re.match(r"^(HG|MG|RG|PG)\s+(\S+)\s+(.+)$", canonical_name)
    assert match, canonical_name
    return match.groups()


def loose(product):
    value = unicodedata.normalize("NFKC", product).upper().replace("Ν", "NU").replace("∀", "TURN A").replace("∞", "INFINITE")
    value = value.replace("THE GUNDAM BASE LIMITED", "GUNDAM BASE LIMITED")
    value = re.sub(r"\bOO\b", "00", value)
    value = re.sub(r"\bO(?=\s+RAISER\b)", "0", value)
    value = re.sub(r"\b(?:19|20)\d{2}\b", " ", value)
    value = re.sub(r"^HG[A-Z:]*\s+", "", value)
    value = re.sub(r"(?<!\w)[A-Z0-9]+(?:[-+/][A-Z0-9]+)+(?!\w)", " ", value)
    tokens = re.findall(r"[A-Z0-9]+", value)
    if len(tokens) > 1 and any(char.isdigit() for char in tokens[0]) and tokens[0] in tokens[1:]:
        tokens.pop(0)
    return "".join(tokens)


def variant_signature(product):
    normalized = re.sub(r"[^A-Z0-9]+", " ", unicodedata.normalize("NFKC", product).upper())
    found = {marker for marker in VARIANTS if marker in normalized}
    found.update(re.findall(r"\bVER\s*(?:KA|\d+(?:\s*\d+)?)\b", normalized))
    return frozenset(found)


def parse_hangar_page(page):
    body = fetch(HANGAR + (f"?page={page}" if page > 1 else ""))
    records = []
    for slug, card in re.findall(r'<a class="group block[^>]+href="/kits/([^"]+)">(.*?)</a>', body, re.S):
        labels = re.findall(r'<img[^>]+alt="([^"]+)"[^>]+class="h-5 w-auto"', card)
        title = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        if not labels or not title:
            continue
        grade_label = html.unescape(labels[0])
        if grade_label.startswith("HG"):
            grade, suffix = "HG", ""
        elif grade_label in {"MG", "RG", "PG"}:
            grade, suffix = grade_label, ""
        elif grade_label == "FM":
            grade, suffix = "MG", " (FULL MECHANICS)"
        elif grade_label == "PGU":
            grade, suffix = "PG", " (PG UNLEASHED)"
        else:
            continue
        scale = html.unescape(labels[1]) if len(labels) > 1 else ""
        product = clean(title.group(1))
        scale_in_name = re.match(r"^(\d+/\d+)\s+(.+)$", product)
        if not scale and scale_in_name:
            scale, product = scale_in_name.groups()
        if scale not in {"1/144", "1/100", "1/60"}:
            continue
        spans = [clean(value) for value in re.findall(r"<span[^>]*>(.*?)</span>", card, re.S)]
        price = next((re.sub(r"\D", "", value) for value in spans if "¥" in value), "")
        year = next((value for value in spans if re.fullmatch(r"\d{4}", value)), "")
        if price:
            product += suffix if suffix and suffix not in product.upper() else ""
            records.append({"canonical": f"{grade} {scale} {product}", "grade": grade, "scale": scale,
                            "product": product, "price": price, "year": year, "source": "hangar", "slug": slug})
    return records


def hangar_records():
    first = fetch(HANGAR)
    total = int(re.search(r'\\"totalCount\\":(\d+)', first).group(1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        pages = list(executor.map(parse_hangar_page, range(1, math.ceil(total / 30) + 1)))
    return [record for page in pages for record in page]


def bandai_records():
    pages, requests = {}, []
    for brand in GLOBAL_BRANDS:
        first = fetch(f"{GLOBAL}brand/{brand}/")
        pages[(brand, 1)] = first
        last = max((int(page) for page in re.findall(r'href="\./\?p=(\d+)"', first)), default=1)
        requests.extend((brand, page) for page in range(2, last + 1))

    def load(item):
        brand, page = item
        return brand, page, fetch(f"{GLOBAL}brand/{brand}/?p={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for brand, page, body in executor.map(load, requests):
            pages[(brand, page)] = body

    records = []
    pattern = r'<a href="https://global\.bandai-hobby\.net/en-us/item/([^/]+)/" class="c-card p-card -landscape">(.*?)</a>'
    for (brand, _), body in pages.items():
        for item_id, card in re.findall(pattern, body, re.S):
            title = re.search(r'<div class="p-card__tit">(.*?)</div>', card, re.S)
            price = re.search(r'<div class="p-card__price">\s*([\d,]+)\s*Yen', card, re.S | re.I)
            date = re.search(r'<div class="p-card_date">.*?(\d{4})\s*</div>', card, re.S)
            parsed = canonicalize(title.group(1), brand) if title else None
            if parsed and price:
                canonical, grade, scale = parsed
                records.append({"canonical": canonical, "grade": grade, "scale": scale, "product": parts(canonical)[2],
                                "price": price.group(1).replace(",", ""), "year": date.group(1) if date else "",
                                "source": "bandai", "slug": item_id})
    return records


def japanese_key(value):
    value = unicodedata.normalize("NFKC", value).upper()
    value = re.sub(r"^(?:HG[A-Z:]*|MG|RG|PG)\s*(?:\d+/\d+)?\s*", "", value)
    return re.sub(r"[^A-Z0-9\u3040-\u30ff\u3400-\u9fff]+", "", value)


def manual_records():
    pages, requests = {}, []
    for category in MANUAL_CATEGORIES:
        first = fetch(f"{MANUAL}?categories%5B0%5D={category}")
        pages[(category, 1)] = first
        count = int(re.search(r"([\d,]+)\u4ef6\u306e\u7d50\u679c", first).group(1).replace(",", ""))
        requests.extend((category, page) for page in range(2, math.ceil(count / 20) + 1))

    def load(item):
        category, page = item
        return category, page, fetch(f"{MANUAL}?categories%5B0%5D={category}&page={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for category, page, body in executor.map(load, requests):
            pages[(category, page)] = body

    records = []
    for (category, _), body in pages.items():
        for item in body.split('<div class="bl_result_item">')[1:]:
            jp = re.search(r'<div class="bl_result_name">\s*(.*?)\s*<span', item, re.S)
            en = re.search(r'<span class="bl_result_name_en">(.*?)</span>', item, re.S)
            date = re.search(r"(\d{4})\u5e74(\d+)\u6708", item)
            parsed = canonicalize(en.group(1), category) if en else None
            if jp and parsed:
                canonical, grade, scale = parsed
                records.append({"canonical": canonical, "grade": grade, "scale": scale, "product": parts(canonical)[2],
                                "japanese": clean(jp.group(1)), "yearmonth": f"{date.group(1)}-{int(date.group(2)):02d}" if date else ""})
    return records


def premium_records():
    brands = {"pb_hg": "HG", "pb_mg": "MG", "pb_rg": "RG", "pb_pg": "PG"}
    pages, requests = {}, []
    for brand in brands:
        first = fetch(f"{PREMIUM}?brand={brand}")
        pages[(brand, 1)] = first
        count = int(re.search(r"\u5168&nbsp;([\d,]+)&nbsp;\u4ef6", first).group(1).replace(",", ""))
        requests.extend((brand, page) for page in range(2, math.ceil(count / 20) + 1))

    def load(item):
        brand, page = item
        return brand, page, fetch(f"{PREMIUM}?brand={brand}&page={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for brand, page, body in executor.map(load, requests):
            pages[(brand, page)] = body

    records = []
    for (brand, _), body in pages.items():
        for item in re.findall(r'<li class="result_item">(.*?)</li>', body, re.S):
            title = re.search(r'<span class="result_itemTitle">(.*?)</span>', item, re.S)
            price = re.search(r'<span class="result_itemPrice">.*?([\d,]+)\u5186', item, re.S)
            date = re.search(r'<span class="result_itemDeliver">\s*(\d{4})\u5e74(\d+)\u6708', item, re.S)
            if title and price:
                records.append({"grade": brands[brand], "japanese": clean(title.group(1)),
                                "price": price.group(1).replace(",", ""),
                                "yearmonth": f"{date.group(1)}-{int(date.group(2)):02d}" if date else "", "source": "premium"})
    return records


def gundam_base_records():
    pages, requests = {}, []
    for grade in ("HG", "MG", "RG", "PG"):
        first = fetch(f"{GUNDAM_BASE}?brand={grade}&paging=1")
        pages[(grade, 1)] = first
        count = int(re.search(r"\u5168([\d,]+)\u4ef6", first).group(1).replace(",", ""))
        requests.extend((grade, page) for page in range(2, math.ceil(count / 20) + 1))

    def load(item):
        grade, page = item
        return grade, page, fetch(f"{GUNDAM_BASE}?brand={grade}&paging={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for grade, page, body in executor.map(load, requests):
            pages[(grade, page)] = body

    records = []
    for (grade, _), body in pages.items():
        for item in re.findall(r'<li id="gbsitem[^>]+>(.*?)</li>', body, re.S):
            title = re.search(r'<p class="name">(.*?)</p>', item, re.S)
            price = re.search(r"\u4fa1\u683c:\s*([\d,]+)\u5186", item)
            date = re.search(r"\u767a\u58f2\u65e5:\s*(\d{4})\u5e74(\d+)\u6708", item)
            if title and price:
                records.append({"grade": grade, "japanese": clean(title.group(1)), "price": price.group(1).replace(",", ""),
                                "yearmonth": f"{date.group(1)}-{int(date.group(2)):02d}" if date else "", "source": "base"})
    return records


def gunpla_in_records():
    paths = {"hg": "HG", "hguc": "HG", "mg": "MG", "rg": "RG", "pg": "PG"}
    pages, requests = {}, []
    for path in paths:
        first = fetch(f"{GUNPLA_IN}/{path}")
        pages[(path, 1)] = first
        count = int(re.search(r"\u73fe\u5728([\d,]+)\u4ef6", first).group(1).replace(",", ""))
        requests.extend((path, page) for page in range(2, math.ceil(count / 50) + 1))

    def load(item):
        path, page = item
        return path, page, fetch(f"{GUNPLA_IN}/{path}?page={page}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for path, page, body in executor.map(load, requests):
            pages[(path, page)] = body

    records = []
    for (path, _), body in pages.items():
        for item in re.findall(r'<section id="data_index_[^"]+" class="search-list">(.*?)</section>', body, re.S):
            title = re.search(r'<h3 class="g-name">.*?<a[^>]+>(.*?)</a>', item, re.S)
            price = re.search(r'<dd class="g-price">\s*\uffe5([\d,]+)', item)
            date = re.search(r'<dd class="g-date">\s*(\d{4})\u5e74(\d+)\u6708', item)
            if title and price:
                records.append({"grade": paths[path], "japanese": clean(title.group(1)), "price": price.group(1).replace(",", ""),
                                "yearmonth": f"{date.group(1)}-{int(date.group(2)):02d}" if date else "", "source": "gunpla_in"})
    return records


def join_japanese(manual, catalog):
    joined = []
    for item in catalog:
        exact = [record for record in manual if record["grade"] == item["grade"]
                 and japanese_key(record["japanese"]) == japanese_key(item["japanese"])]
        candidates = exact
        if not candidates and item["yearmonth"]:
            dated = [record for record in manual if record["grade"] == item["grade"] and record["yearmonth"] == item["yearmonth"]]
            scored = sorted(((SequenceMatcher(None, japanese_key(item["japanese"]), japanese_key(record["japanese"])).ratio(), record)
                             for record in dated), reverse=True, key=lambda pair: pair[0])
            if scored and scored[0][0] >= 0.9 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.04):
                candidates = [scored[0][1]]
        if candidates:
            record = max(candidates, key=lambda candidate: candidate["yearmonth"])
            joined.append({**record, "price": item["price"], "year": item["yearmonth"], "source": item["source"],
                           "slug": japanese_key(item["japanese"])})
    return joined


def write_migration(rows):
    values = ",\n".join(
        f"    ('{row['canonical_name'].replace(chr(39), chr(39) * 2)}', {row['msrp']})"
        for row in rows if row["msrp"]
    )
    sql = f"""update public.products as product
set msrp = source.msrp,
    msrp_currency = 'JPY'
from (values
{values}
) as source(canonical_name, msrp)
where product.canonical_name = source.canonical_name;

create unique index if not exists products_canonical_name_uidx
on public.products (canonical_name);
"""
    path = Path(OUT) / "migrations" / "20260818020000_backfill_product_msrp.sql"
    path.write_text(sql, encoding="utf-8", newline="\n")
    return path


def choose(row, source, allow_fuzzy=True):
    grade, scale, product = parts(row["canonical_name"])
    candidates = [record for record in source if record["grade"] == grade and record["scale"] == scale]
    exact = [record for record in candidates if key(record["canonical"]) == key(row["canonical_name"])]
    if exact:
        return {**max(exact, key=lambda record: record["year"]), "match": "exact"}
    same = [record for record in candidates if loose(record["product"]) == loose(product)
            and variant_signature(record["product"]) == variant_signature(product)]
    if same:
        return {**max(same, key=lambda record: record["year"]), "match": "loose"}
    if not allow_fuzzy or not row["original_release_date"] or row["canonical_name"] in FUZZY_EXCEPTIONS:
        return None
    year = row["original_release_date"][:4]
    dated = [record for record in candidates if record["year"] == year
             and variant_signature(record["product"]) == variant_signature(product)]
    scored = sorted(((SequenceMatcher(None, loose(product), loose(record["product"])).ratio(), record)
                     for record in dated), reverse=True, key=lambda item: item[0])
    if not scored or scored[0][0] < 0.86 or (len(scored) > 1 and scored[0][0] - scored[1][0] < 0.04):
        return None
    return {**scored[0][1], "match": "fuzzy"}


def main():
    files = sorted(glob.glob(str(OUT / "products_batch_*.csv")), key=lambda path: int(re.search(r"(\d+)\.csv$", path).group(1)))
    batches = []
    for path in files:
        with open(path, encoding="utf-8-sig", newline="") as source:
            batches.append((path, list(csv.DictReader(source))))
    rows = [row for _, batch in batches for row in batch]
    before = sum(bool(row["msrp"]) for row in rows)
    if "--migration-only" in sys.argv:
        assert len(rows) == len({row["canonical_name"] for row in rows})
        assert before / len(rows) >= 0.8
        print(f"migration={write_migration(rows)} rows={before}")
        return
    hangar, bandai = hangar_records(), bandai_records()
    manual = manual_records()
    gunpla_in = join_japanese(manual, gunpla_in_records())
    premium = join_japanese(manual, premium_records())
    base = join_japanese(manual, gundam_base_records())
    matched = {"hangar": 0, "gunpla_in": 0, "bandai": 0, "premium": 0, "base": 0}
    audit = []
    for row in rows:
        if not row["msrp"]:
            record = choose(row, hangar)
            if record:
                row["msrp"] = record["price"]
                matched["hangar"] += 1
                if record["match"] == "fuzzy":
                    audit.append((row["canonical_name"], record["canonical"], record["slug"]))
        if not row["msrp"]:
            record = choose(row, gunpla_in, allow_fuzzy=False)
            if record:
                row["msrp"] = record["price"]
                matched["gunpla_in"] += 1
        for source_name, source in (("bandai", bandai), ("premium", premium), ("base", base)):
            record = choose(row, source, allow_fuzzy=False)
            if record and row["msrp"] != record["price"]:
                row["msrp"] = record["price"]
                matched[source_name] += 1

    names = [row["canonical_name"] for row in rows]
    assert len(names) == len(set(names)), "duplicate canonical_name"
    assert all(row["grade"] in {"HG", "MG", "RG", "PG"} for row in rows)
    assert all(not row["msrp"] or re.fullmatch(r"\d+(?:\.\d+)?", row["msrp"]) for row in rows)
    assert all(not row[field] or re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[field])
               for row in rows for field in ("original_release_date", "last_reproduction_date"))
    after = sum(bool(row["msrp"]) for row in rows)
    print(f"rows={len(rows)} msrp={before}->{after} coverage={after / len(rows):.1%} matches={matched} "
          f"sources=hangar:{len(hangar)},gunpla_in:{len(gunpla_in)},bandai:{len(bandai)},premium:{len(premium)},base:{len(base)} "
          f"write={'--write' in sys.argv}")
    if "--debug" in sys.argv:
        for local, source, slug in audit:
            print(f"FUZZY\t{local}\t{source}\t{slug}")
        for row in (row for row in rows if not row["msrp"]):
            grade, scale, product = parts(row["canonical_name"])
            year = row["original_release_date"][:4]
            candidates = [record for record in hangar if record["grade"] == grade and record["scale"] == scale and record["year"] == year]
            scored = sorted(((SequenceMatcher(None, loose(product), loose(record["product"])).ratio(), record) for record in candidates),
                            reverse=True, key=lambda item: item[0])
            if scored and scored[0][0] >= 0.65:
                print(f"{scored[0][0]:.2f}\t{row['canonical_name']}\t{scored[0][1]['canonical']}")
    assert after / len(rows) >= 0.8, f"MSRP coverage only {after / len(rows):.1%}; refusing to write"
    if "--write" in sys.argv:
        for path, batch in batches:
            with open(path, "w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=HEADERS, lineterminator="\r\n")
                writer.writeheader()
                writer.writerows(batch)
    print(f"fuzzy_audit={len(audit)}")


if __name__ == "__main__":
    main()
