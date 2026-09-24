import json
import time
import requests

from wlc import Weblate, Project, Component, Unit, Translation

UNTRANSLATED = 0
NEEDS_EDITING = 10
TRANSLATED = 20
APPROVED = 30
READONLY = 100

with open("APIKEY.json", "r", encoding="utf-8") as file:
    api_key = json.load(file)

BASE = "https://calcqvtdldqwqewvqhur.supabase.co/functions/v1"
H = {"Authorization": f"Bearer {api_key["leemeta"]}", "Content-Type": "application/json"}

def translate(segments: list[str], source_lang, target_lang) -> list[str]:
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
    return [out["translations"][0]["target"]]


client = Weblate(
    url="https://hosted.weblate.org/api/",
    key=api_key["weblate"],
)

#project = client.get_project("fluidd")
#component_url = project["components_list_url"]
#component = client.get_component("fluidd/fluidd")
translations = Translation(client, "https://hosted.weblate.org/api/translations/fluidd/fluidd/sl/")
units = list(translations.units())

for unit in units:
    if unit["state"] == UNTRANSLATED:
        source = unit["source"]
        translated = translate(source, source_lang="en", target_lang="sl")
        unit.patch(state=NEEDS_EDITING, target=translated)
        print(f"Source: {unit['source'][0]}, Target: {translated[0]}")
