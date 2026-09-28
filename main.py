import json
import time
import requests

from wlc import Weblate, Translation

UNTRANSLATED = 0
NEEDS_EDITING = 10
TRANSLATED = 20
APPROVED = 30
READONLY = 100

with open("APIKEY.json", "r", encoding="utf-8") as file:
    api_key = json.load(file)

BASE = "https://calcqvtdldqwqewvqhur.supabase.co/functions/v1"
H = {"Authorization": f"Bearer {api_key["leemeta"]}", "Content-Type": "application/json"}

def translate_segments(segments: list[str], source_lang, target_lang) -> list[str]:
    # 1) Submit
    r = requests.post(f"{BASE}/api-translate-submit", headers=H, timeout=10, json={
        "source_lang": source_lang,
        "target_lang": target_lang,
        "segments": segments,
    }).json()
    req_id = r["request_id"]

    # 2) Poll
    while True:
        s = requests.get(f"{BASE}/api-translate-status", params={"id": req_id}, headers=H, timeout=10).json()
        if s["status"] not in ("queued", "processing"):
            break
        time.sleep(2)

    # 3) Get translations
    out = requests.get(f"{BASE}/api-get-translations", params={"id": req_id}, headers=H, timeout=10).json()
    out = [translation["target"] for translation in out["translations"]]
    return out


client = Weblate(
    url="https://hosted.weblate.org/api/",
    key=api_key["weblate"],
)

def get_untranslated_units(project_url: str) -> list[dict]:
    translations = Translation(client, project_url)
    units = list(translations.units())

    untranslated_units = []
    for unit in units:
        if unit["state"] == UNTRANSLATED:
            untranslated_units.append(unit)

    return untranslated_units

projects = ["https://hosted.weblate.org/api/translations/fluidd/fluidd/sl/",
            "https://hosted.weblate.org/api/translations/remmina/remmina/sl/",
            "https://hosted.weblate.org/api/translations/spoolman/spoolman-web-ui-v2/sl/"]

for project in projects:
    untranslated_units = get_untranslated_units(project)

    untranslated_chunks = []
    chunk_size = 100
    for i in range(0, len(untranslated_units), chunk_size):
        untranslated_chunks.append(untranslated_units[i:i + chunk_size])

    for chunk in untranslated_chunks:
        sources = []
        units_to_translate = []
        for unit in chunk:
            if len(unit["source"]) == 1:
                sources.extend(unit["source"])  # do not translate multi-line segments (plural)
                units_to_translate.append(unit)

        if sources:
            translated_segments = translate_segments(sources, source_lang="en", target_lang="sl")

            for unit in units_to_translate:
                target_list = [translated_segments[0]]
                del translated_segments[0]
                #print(f"Source: {unit['source']}, Target: {target_list}")
                unit.patch(state=NEEDS_EDITING, target=target_list)

print("Konec")
