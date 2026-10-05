from modules.scraper.base.radancy_scraper import RadancyScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

SEARCH_PARAMS = {
    'ActiveFacetID': '9378800',
    'Distance': 50,
    'RadiusUnitType': 0,
    'Keywords': '',
    'Location': '',
    'ShowRadius': 'False',
    'CustomFacetName': '',
    'FacetTerm': '',
    'FacetType': 0,
    'FacetFilters[0].ID': '1269750',
    'FacetFilters[0].FacetType': 2,
    'FacetFilters[0].Display': 'India',
    'FacetFilters[0].IsApplied': 'true',
    'FacetFilters[0].FieldName': '',
    'SearchResultsModuleName': 'Search Results',
    'SearchFiltersModuleName': 'Search Filters',
    'SortCriteria': 5,
    'SortDirection': 1,
    'SearchType': 5,
    'PostalCode': '',
    'ResultsType': 0,
}

@register_scraper
class CitiScraper(RadancyScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.CITI

    @property
    def host(self) -> str:
        return 'jobs.citi.com'

    @property
    def company_name(self) -> str:
        return 'Citi'

    @property
    def search_params(self) -> dict:
        return SEARCH_PARAMS
