"""Pre-translate every disease description into translations_cache.json.

Run once after changing DISEASE_DESCRIPTIONS so language switching in the app is
instant:  python warm_translations.py
"""
import time

import app

LANGS = ["hi", "kn", "te", "ta"]


def main():
    missing = []
    for lang in LANGS:
        for disease, description in app.DISEASE_DESCRIPTIONS.items():
            for attempt in range(3):
                english_only = app.translate_text_preserve_links(description, lang) == description
                if not english_only:
                    break
                time.sleep(5 * (attempt + 1))  # Google rate limit: back off and retry
            else:
                missing.append(f"{lang}: {disease}")
            print(f"{lang} {disease}: {'missing' if english_only else 'ok'}", flush=True)
            time.sleep(0.5)
    print(f"\n{len(app.TRANSLATIONS.get('hi', {}))} hi entries saved to {app.TRANSLATIONS_PATH}")
    if missing:
        print("Still untranslated (re-run later):", *missing, sep="\n  ")


if __name__ == "__main__":
    main()
