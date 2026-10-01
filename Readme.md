# Automatic translator for Weblate

This project automatically translates untranslated straings on Weblate and sets status for review. A human has to review the final translation.

# How to use

## 1. Create python venv and install Weblate API
- Create venv `python -m venv .venv`
- Install **Weblate Client** `pip install wlc`
- Install **Requests** `pip install requests`

## 2. Get API key
Go to [https://hosted.weblate.org](https://hosted.weblate.org), User -> Settings -> API access and get your API key.

# Config file schema

```JSON
{
    "api_keys": {
        "leemeta": "",
        "weblate": ""
    },
    "projects": [
        {
            "name": "",
            "source_lang": "",
            "target_lang": "",
            "translations_link": ""
        },
        {
            ...
        }
        ...
    ]
}
```
