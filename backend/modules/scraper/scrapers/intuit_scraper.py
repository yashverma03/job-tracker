from modules.scraper.base.radancy_scraper import RadancyScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

SEARCH_PARAMS = {
    'ActiveFacetID': '1269750',
    'Distance': 5000,
    'RadiusUnitType': 0,
    'Keywords': '',
    'Location': '',
    'ShowRadius': 'False',
    'CustomFacetName': '',
    'FacetTerm': '',
    'FacetType': 0,
    'FacetFilters[0].ID': '68338',
    'FacetFilters[0].FacetType': 1,
    'FacetFilters[0].Display': 'Data',
    'FacetFilters[0].IsApplied': 'true',
    'FacetFilters[0].FieldName': '',
    'FacetFilters[1].ID': '68347',
    'FacetFilters[1].FacetType': 1,
    'FacetFilters[1].Display': 'Information Technology',
    'FacetFilters[1].IsApplied': 'true',
    'FacetFilters[1].FieldName': '',
    'FacetFilters[2].ID': '68357',
    'FacetFilters[2].FacetType': 1,
    'FacetFilters[2].Display': 'Software Engineering',
    'FacetFilters[2].IsApplied': 'true',
    'FacetFilters[2].FieldName': '',
    'FacetFilters[3].ID': '1269750',
    'FacetFilters[3].FacetType': 2,
    'FacetFilters[3].Display': 'India',
    'FacetFilters[3].IsApplied': 'true',
    'FacetFilters[3].FieldName': '',
    'SearchResultsModuleName': 'Search Results',
    'SearchFiltersModuleName': 'Search Filters',
    'SortCriteria': 0,
    'SortDirection': 0,
    'SearchType': 5,
    'PostalCode': '',
    'ResultsType': 0,
}


@register_scraper
class IntuitScraper(RadancyScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.INTUIT

    @property
    def host(self) -> str:
        return 'jobs.intuit.com'

    @property
    def company_name(self) -> str:
        return 'Intuit'

    @property
    def search_params(self) -> dict:
        return SEARCH_PARAMS
