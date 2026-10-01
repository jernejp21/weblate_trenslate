import time
import requests

from wlc import Weblate, Translation

UNTRANSLATED = 0
NEEDS_EDITING = 10
TRANSLATED = 20
APPROVED = 30
READONLY = 100

LEEBUDY_BASE_URL = "https://calcqvtdldqwqewvqhur.supabase.co/functions/v1" # LeeBudy AI url
WEBLATE_URL = "https://hosted.weblate.org/api/" # Weblate url


class Translator:
    def __init__(self, api_keys: dict):
        self.api_keys = api_keys

    def translate_projects(self, projects: list[dict]):
        for project in projects:
            untranslated_units = self.get_untranslated_units(project["translations_link"])

            untranslated_chunks = []
            chunk_size = 100
            for i in range(0, len(untranslated_units), chunk_size):
                untranslated_chunks.append(untranslated_units[i:i + chunk_size])

            for chunk in untranslated_chunks:
                sources = []
                units_to_translate = []
                for unit in chunk:
                    if len(unit["source"]) == 1:
                        # do not translate multi-line segments (plural)
                        sources.extend(unit["source"])
                        units_to_translate.append(unit)

                if sources:
                    translated_segments = self.translate_segments(sources,
                                                                  project["source_lang"],
                                                                  project["target_lang"])

                    for unit in units_to_translate:
                        target_list = [translated_segments[0]]
                        del translated_segments[0]
                        #print(f"Source: {unit['source']}, Target: {target_list}")
                        unit.patch(state=NEEDS_EDITING, target=target_list)

    def translate_segments(self, segments: list[str], source_lang, target_lang) -> list[str]:
        api_key = self.api_keys["leemeta"]
        header = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        # 1) Submit
        response = requests.post(f"{LEEBUDY_BASE_URL}/api-translate-submit", headers=header,
                                 timeout=10,
                                 json={"source_lang": source_lang,
                                       "target_lang": target_lang,
                                       "segments": segments}).json()
        req_id = response["request_id"]

        # 2) Poll
        while True:
            response = requests.get(f"{LEEBUDY_BASE_URL}/api-translate-status",
                                    params={"id": req_id},
                                    headers=header, timeout=10).json()

            if response["status"] not in ("queued", "processing"):
                break
            time.sleep(2)

        # 3) Get translations
        out = requests.get(f"{LEEBUDY_BASE_URL}/api-get-translations", params={"id": req_id},
                           headers=header, timeout=10).json()
        out = [translation["target"] for translation in out["translations"]]
        return out


    def get_untranslated_units(self, project_url: str) -> list[dict]:
        api_key = self.api_keys["weblate"]
        client = Weblate(url=WEBLATE_URL, key=api_key)
        translations = Translation(client, project_url)
        units = list(translations.units())

        untranslated_units = []
        for unit in units:
            if unit["state"] == UNTRANSLATED:
                untranslated_units.append(unit)

        return untranslated_units
