import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import pymupdf


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY_ROOT / "docs" / "reference" / "AX25.2.2-Jul-98.pdf"
OUTPUT = REPOSITORY_ROOT / "docs" / "reference" / "AX25.2.2-Jul-98-TH.pdf"
CACHE = REPOSITORY_ROOT / "tmp" / "translation_cache.json"
FONT_DIR = Path(r"C:\Windows\Fonts")

PRESERVE_TOKENS = {
    "AX.25", "LAPB", "HDLC", "ASCII", "CRC", "FCS", "PID", "SSID",
    "SABM", "SABME", "DISC", "DM", "UA", "FRMR", "XID", "TEST",
    "RR", "RNR", "REJ", "SREJ", "UI", "TAPR", "ISO", "OSI",
    "N(R)", "N(S)", "P/F", "C/R", "V(R)", "V(S)", "V(A)",
}


def block_text(block):
    return "\n".join(
        "".join(span.get("text", "") for span in line.get("spans", []))
        for line in block.get("lines", [])
    ).strip()


def needs_translation(text):
    probe = text
    for token in sorted(PRESERVE_TOKENS, key=len, reverse=True):
        probe = re.sub(re.escape(token), "", probe, flags=re.IGNORECASE)
    probe = re.sub(r"(?:mailto:)?[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "", probe, flags=re.IGNORECASE)
    probe = re.sub(r"https?://\S+|www\.\S+", "", probe, flags=re.IGNORECASE)
    probe = re.sub(r"\b(?:0x[0-9A-Fa-f]+|[01]{4,})\b", "", probe)
    return bool(re.search(r"[A-Za-z]{2,}", probe))


def mask_tokens(text):
    mapping = {}
    ordered = sorted(PRESERVE_TOKENS, key=len, reverse=True)
    pattern = re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(re.escape(x) for x in ordered) + r")(?![A-Za-z0-9])"
    )

    def repl(match):
        key = f"ZXKEEP{len(mapping):03d}ZX"
        mapping[key] = match.group(0)
        return key

    text = re.sub(r"(?:mailto:)?[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", repl, text, flags=re.IGNORECASE)
    text = re.sub(r"https?://\S+|www\.\S+", repl, text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:0x[0-9A-Fa-f]+|[01]{4,})\b", repl, text)
    return pattern.sub(repl, text), mapping


def restore_tokens(text, mapping):
    for key, value in mapping.items():
        text = re.sub(re.escape(key), value, text, flags=re.IGNORECASE)
    return text


def split_long(text, max_chars=2600):
    if len(text) <= max_chars:
        return [text]
    pieces = []
    remaining = text
    while len(remaining) > max_chars:
        cut = max(
            remaining.rfind("\n", 0, max_chars),
            remaining.rfind(". ", 0, max_chars),
            remaining.rfind("; ", 0, max_chars),
            remaining.rfind(" ", 0, max_chars),
        )
        if cut < max_chars // 2:
            cut = max_chars
        elif remaining[cut:cut + 2] in (". ", "; "):
            cut += 1
        pieces.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def google_translate(text, retries=5):
    payload = urllib.parse.urlencode(
        {"client": "gtx", "sl": "en", "tl": "th", "dt": "t", "q": text}
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://translate.googleapis.com/translate_a/single",
        data=payload,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
            return "".join(item[0] for item in data[0] if item and item[0] is not None)
        except Exception as exc:
            last_error = exc
            time.sleep(min(2 ** attempt, 12))
    raise RuntimeError(f"Google translation failed after {retries} attempts: {last_error}")


def batch_translate(items, cache):
    # items: list of (stable_id, source_text)
    pending_parts = []
    part_meta = {}
    for stable_id, source_text in items:
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        cached = cache.get(stable_id)
        if cached and cached.get("source_hash") == source_hash:
            continue
        masked, token_map = mask_tokens(source_text)
        parts = split_long(masked)
        part_ids = []
        for index, part in enumerate(parts):
            part_id = f"{stable_id}::part{index}"
            part_ids.append(part_id)
            pending_parts.append((part_id, part))
        part_meta[stable_id] = {
            "source_hash": source_hash,
            "part_ids": part_ids,
            "token_map": token_map,
        }

    translated_parts = {}
    cursor = 0
    while cursor < len(pending_parts):
        batch = []
        char_count = 0
        while cursor < len(pending_parts):
            candidate = pending_parts[cursor]
            added = len(candidate[1]) + 30
            if batch and char_count + added > 3600:
                break
            batch.append(candidate)
            char_count += added
            cursor += 1

        combined = batch[0][1]
        for local_index, (_, text) in enumerate(batch[1:], start=1):
            combined += f"\n<<<SEGMENT_{local_index:04d}>>>\n" + text
        result = google_translate(combined)
        pieces = re.split(r"\n?\s*<<<\s*SEGMENT_(\d{4})\s*>>>\s*\n?", result)
        recovered = [pieces[0]]
        if len(batch) > 1:
            for i in range(1, len(pieces), 2):
                recovered.append(pieces[i + 1])
        if len(recovered) != len(batch):
            recovered = [google_translate(text) for _, text in batch]
        for (part_id, _), translated in zip(batch, recovered):
            translated_parts[part_id] = translated.strip()
        print(f"translated {cursor}/{len(pending_parts)} parts", flush=True)

    for stable_id, meta in part_meta.items():
        translated = "\n".join(translated_parts[x] for x in meta["part_ids"])
        translated = restore_tokens(translated, meta["token_map"])
        cache[stable_id] = {
            "source_hash": meta["source_hash"],
            "translation": translated,
        }
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return cache


def dominant_style(unit):
    spans = [span for span in unit.get("spans", []) if span.get("text")]
    if not spans:
        return 10.0, False, False, "#000000"
    weighted_sizes = []
    for span in spans:
        weighted_sizes.extend([round(float(span.get("size", 10)), 1)] * max(1, len(span.get("text", ""))))
    size = Counter(weighted_sizes).most_common(1)[0][0]
    font = Counter(
        span.get("font", "") for span in spans for _ in range(max(1, len(span.get("text", ""))))
    ).most_common(1)[0][0]
    color_value = int(Counter(
        span.get("color", 0) for span in spans for _ in range(max(1, len(span.get("text", ""))))
    ).most_common(1)[0][0])
    color = f"#{color_value & 0xFFFFFF:06x}"
    return size, "Bold" in font, "Italic" in font or "Oblique" in font, color


def block_alignment(page, unit):
    rect = pymupdf.Rect(unit["bbox"])
    parent = pymupdf.Rect(unit["parent_bbox"])
    if parent.width < page.rect.width * 0.72:
        if abs((rect.x0 + rect.x1) / 2 - page.rect.width / 2) < 34:
            return "center"
    return "left"


def insert_translation(page, unit, translated, archive):
    rect = pymupdf.Rect(unit["bbox"])
    parent = pymupdf.Rect(unit["parent_bbox"])
    # Paragraph and contents lines may use the remainder of their original text column.
    if parent.width > page.rect.width * 0.54 and unit.get("parent_line_count", 0) > 2:
        rect.x1 = parent.x1
    # A tiny expansion avoids clipping accents at the original tight text boundary.
    rect.x0 = max(page.rect.x0, rect.x0 - 0.8)
    rect.x1 = min(page.rect.x1, rect.x1 + 0.8)
    rect.y0 = max(page.rect.y0, rect.y0 - 0.6)
    rect.y1 = min(page.rect.y1, rect.y1 + 1.2)
    size, bold, italic, color = dominant_style(unit)
    alignment = block_alignment(page, unit)
    weight = "700" if bold else "400"
    style = "italic" if italic else "normal"
    body = html.escape(translated).replace("\n", "<br>")
    css = f"""
        @font-face {{font-family: ThaiDoc; src: url(tahoma.ttf); font-weight: 400;}}
        @font-face {{font-family: ThaiDoc; src: url(tahomabd.ttf); font-weight: 700;}}
        * {{font-family: ThaiDoc; font-size: {size}pt; font-weight: {weight};
            font-style: {style}; color: {color}; line-height: 1.08;}}
        div {{margin: 0; padding: 0; text-align: {alignment};}}
    """
    spare, scale = page.insert_htmlbox(
        rect,
        f"<div>{body}</div>",
        css=css,
        scale_low=0.42,
        archive=archive,
        overlay=True,
    )
    return spare, scale


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    doc = pymupdf.open(SOURCE)
    limit = min(doc.page_count, args.max_pages) if args.max_pages else doc.page_count
    page_units = []
    items = []
    for page_index in range(limit):
        units = []
        for block_index, block in enumerate(doc[page_index].get_text("dict").get("blocks", [])):
            if block.get("type") != 0:
                continue
            lines = block.get("lines", [])
            for line_index, line in enumerate(lines):
                text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if not text or not needs_translation(text):
                    continue
                stable_id = f"page{page_index + 1:03d}-block{block_index:03d}-line{line_index:03d}"
                unit = {
                    "bbox": line.get("bbox", block["bbox"]),
                    "spans": line.get("spans", []),
                    "parent_bbox": block["bbox"],
                    "parent_line_count": len(lines),
                }
                units.append((stable_id, unit, text))
                items.append((stable_id, text))
        page_units.append(units)

    cache = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    cache = batch_translate(items, cache)

    archive = pymupdf.Archive(str(FONT_DIR))
    fit_warnings = []
    for page_index, units in enumerate(page_units):
        page = doc[page_index]
        for _, unit, _ in units:
            page.add_redact_annot(unit["bbox"], fill=None, cross_out=False)
        if units:
            page.apply_redactions(images=0, graphics=0, text=0)
        for stable_id, unit, _ in units:
            translated = cache[stable_id]["translation"]
            spare, scale = insert_translation(page, unit, translated, archive)
            if spare < 0 or scale < 0.55:
                fit_warnings.append((page_index + 1, stable_id, round(spare, 2), round(scale, 3)))
        if (page_index + 1) % 10 == 0 or page_index + 1 == limit:
            print(f"laid out {page_index + 1}/{limit} pages", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()
    metadata = doc.metadata or {}
    metadata["title"] = "AX.25 Link Access Protocol for Amateur Packet Radio - ฉบับแปลภาษาไทย"
    doc.set_metadata(metadata)
    doc.save(args.output, garbage=4, deflate=True, clean=True)
    doc.close()
    print(f"OUTPUT={args.output}")
    print(f"FIT_WARNINGS={len(fit_warnings)}")
    for warning in fit_warnings[:100]:
        print("FIT", warning)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
