import json

with open('gui_manager.py', 'r', encoding='utf-8') as file:
    lines = file.readlines()

translations = []
for line in lines:
    if '_l("' in line:
        translation_list = line.split('_l("')[1:]
        for translation in translation_list:
            translate_string = translation.split('")')[0]
            translations.append(translate_string)

en_json = {}

for translation in translations:
    if translation not in en_json:
        print(f"Translation '{translation}' is missing in en.json")
        en_json[translation] = translation
        

with open('i18n/en.json', "w", encoding="utf-8") as file:
    json.dump(en_json, file, indent=4, ensure_ascii=False)



    
print("Konec")
