from modules.scraper.base.radancy_scraper import RadancyScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

SEARCH_PARAMS = {
    'ActiveFacetID': '8604160',
    'Distance': 50,
    'RadiusUnitType': 0,
    'Keywords': '',
    'Location': 'India',
    'ShowRadius': 'False',
    'FacetFilters[0].ID': '8604160',
    'FacetFilters[0].FacetType': 1,
    'FacetFilters[0].Display': 'Engineering',
    'FacetFilters[0].IsApplied': 'true',
    'FacetFilters[1].ID': '8604176',
    'FacetFilters[1].FacetType': 1,
    'FacetFilters[1].Display': 'Information Technology',
    'FacetFilters[1].IsApplied': 'true',
    'FacetFilters[2].ID': '8604192',
    'FacetFilters[2].FacetType': 1,
    'FacetFilters[2].Display': 'Software Engineering',
    'FacetFilters[2].IsApplied': 'true',
    'FacetFilters[3].ID': '1269750',
    'FacetFilters[3].FacetType': 2,
    'FacetFilters[3].Display': 'India',
    'FacetFilters[3].IsApplied': 'true',
    'SearchResultsModuleName': 'Search Results',
    'SearchFiltersModuleName': 'Search Filters',
    'SortCriteria': 2,
    'SortDirection': 0,
    'SearchType': 6,
    'OrganizationIds': '27600',
    'ResultsType': 0,
}

@register_scraper
class NetappScraper(RadancyScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.NETAPP

    @property
    def host(self) -> str:
        return 'careers.netapp.com'

    @property
    def company_name(self) -> str:
        return 'NetApp'

    @property
    def search_params(self) -> dict:
        return SEARCH_PARAMS
