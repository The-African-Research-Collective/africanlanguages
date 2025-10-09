from pprint import pprint
from typing import Optional

from cyclopts import App

import africanlanguages
from africanlanguages import get_all_language_families, get_all_languages, get_language_count, search_languages

app = App()


@app.command()
def main():
    """
    Main entrypoint - shows basic information.
    """
    count = get_language_count()
    print("African Languages Database")
    print(f"Total languages: {count}")
    print("Use --help to see available commands")


@app.command()
def list_languages(limit: int = 20, country: Optional[str] = None, region: Optional[str] = None):
    """
    List languages with optional filtering.

    Args:
        limit: Maximum number of languages to display.
        country: Filter by country name.
        region: Filter by region name.
    """
    if country and country.isnumeric():
        print("Error: Country name cannot be a number.")
        return
    if region and region.isnumeric():
        print("Error: Region name cannot be a number.")
        return

    if country:
        languages = africanlanguages.get_languages_by_country(country)
        if not languages:
            print(f"No languages found for country '{country}'.")
            return
        print(f"Languages spoken in {country}:")
    elif region:
        languages = africanlanguages.get_languages_by_region(region)
        if not languages:
            print(f"No languages found for region '{region}'.")
            return
        print(f"Languages spoken in {region}:")
    else:
        languages = get_all_languages()
        print("All languages:")

    if not languages:
        print("No languages found.")
        return

    for lang in languages[:limit]:
        pprint(lang)

    if len(languages) > limit:
        print(f"... and {len(languages) - limit} more")


@app.command()
def search(query: str):
    """
    Search languages by name or code.

    Args:
        query: The search query string.
    """
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
    """
    Get detailed information about a specific language.

    Args:
        code: The language code (ISO 639-3 or Glottocode).
    """
    lang = africanlanguages.get_language_by_code(code)
    if lang:
        pprint(lang)
    else:
        print(f"Language with code '{code}' not found")


@app.command()
def families():
    """
    List all language families.
    """
    families_list = get_all_language_families()
    print(f"Found {len(families_list)} language families:")
    for family in families_list:
        print(f"  - {family}")


if __name__ == "__main__":
    app()
