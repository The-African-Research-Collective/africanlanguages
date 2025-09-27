from pprint import pprint
from typing import Optional

from cyclopts import App

import africanlanguages
from africanlanguages import get_all_languages, get_language_count, search_languages

app = App()


@app.command()
def main():
    """Main entrypoint - shows basic information"""
    count = get_language_count()
    print("African Languages Database")
    print(f"Total languages: {count}")
    print("Use --help to see available commands")


@app.command()
def list_languages(limit: int = 20, country: Optional[str] = None, region: Optional[str] = None):
    """List languages with optional filtering"""
    if country:
        languages = africanlanguages.get_languages_by_country(country)
        print(f"Languages spoken in {country}:")
    elif region:
        languages = africanlanguages.get_languages_by_region(region)
        print(f"Languages spoken in {region}:")
    else:
        languages = get_all_languages()
        print("All languages:")

    for lang in languages[:limit]:
        pprint(lang)

    if len(languages) > limit:
        print(f"... and {len(languages) - limit} more")


@app.command()
def search(query: str):
    """Search languages by name or code"""
    results = search_languages(query)
    if results:
        print(f"Found {len(results)} languages matching '{query}':")
        for lang in results[:10]:
            pprint(lang)
        if len(results) > 10:
            print(f"... and {len(results) - 10} more")
    else:
        print(f"No languages found matching '{query}'")


@app.command()
def info(code: str):
    """Get detailed information about a specific language"""
    lang = africanlanguages.get_language_by_code(code)
    if lang:
        pprint(lang)
    else:
        print(f"Language with code '{code}' not found")


if __name__ == "__main__":
    app()
