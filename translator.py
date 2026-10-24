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
WEBLATE_TIMEOUT = 60 # Weblate timeout in seconds


class Translator:
    def __init__(self, api_keys: dict, chunk_size: int = 100):
        self.api_keys = api_keys
        self.chunk_size = chunk_size

    def translate_project(self, project_url: str, max_units: int = 1):
        remaining_units = max_units
        if remaining_units == 0:
            return
        untranslated_units = self.get_untranslated_units(project_url)
        if remaining_units is not None:
            untranslated_units = untranslated_units[:remaining_units]
            remaining_units -= len(untranslated_units)

        untranslated_chunks = []
        for i in range(0, len(untranslated_units), self.chunk_size):
            untranslated_chunks.append(untranslated_units[i:i + self.chunk_size])

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
                                                                project_url["source_lang"],
                                                                project_url["target_lang"])

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
        client = Weblate(url=WEBLATE_URL, key=api_key, timeout=WEBLATE_TIMEOUT)
        translations = Translation(client, project_url)
        units = list(translations.units())

        untranslated_units = []
        for unit in units:
            if unit["state"] == UNTRANSLATED:
                untranslated_units.append(unit)

        return untranslated_units

    def reset_needs_editing(self, project_url: str, reset_units_size: int = 10) -> int:
        reset_count = 0
        api_key = self.api_keys["weblate"]
        client = Weblate(url=WEBLATE_URL, key=api_key, timeout=WEBLATE_TIMEOUT)
        translations = Translation(client, project_url)
        units = list(translations.units())

        for unit in units:
            if unit["state"] == NEEDS_EDITING and len(unit["source"]) == 1:
                if reset_count >= reset_units_size:
                    break
                # do not translate multi-line segments (plural)
                unit.patch(state=UNTRANSLATED, target=[""])
                reset_count += 1

        return reset_count

    def get_project_status(self, project_url: str) -> dict[str, int]:
        api_key = self.api_keys["weblate"]
        client = Weblate(url=WEBLATE_URL, key=api_key, timeout=WEBLATE_TIMEOUT)
        translations = Translation(client, project_url)
        units = list(translations.units())

        return {
            "total": len(units),
            "translated": sum(unit["state"] == TRANSLATED for unit in units),
            "untranslated": sum(unit["state"] == UNTRANSLATED for unit in units),
            "needs_editing": sum(unit["state"] == NEEDS_EDITING for unit in units),
        }
