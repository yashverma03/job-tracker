from modules.scraper.base.radancy_scraper import RadancyScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'jobs.paloaltonetworks.com'
COMPANY_NAME = 'Palo Alto Networks'

CATEGORY_FACETS = (
    ('9427536', 'Identity Security Customer Success Engineering'),
    ('9376368', 'InfoSec'),
    ('9376352', 'IT'),
    ('9376336', 'Product Engineering'),
)
INDIA_FACET = ('1269750', 'India')


def _build_search_params() -> dict:
    params = {
        'ActiveFacetID': '9376352',
        'Distance': 50,
        'RadiusUnitType': 0,
        'Keywords': '',
        'Location': '',
        'ShowRadius': 'False',
    }
    facets = [(facet_id, display, 1) for facet_id, display in CATEGORY_FACETS]
    facets.append((*INDIA_FACET, 2))
    for index, (facet_id, display, facet_type) in enumerate(facets):
        prefix = f'FacetFilters[{index}]'
        params.update(
            {
                f'{prefix}.ID': facet_id,
                f'{prefix}.FacetType': facet_type,
                f'{prefix}.Display': display,
                f'{prefix}.IsApplied': 'true',
                f'{prefix}.FieldName': '',
            }
        )
    params.update(
        {
            'SearchResultsModuleName': 'Section 29 - Search Results',
            'SearchFiltersModuleName': 'Section 29 - Search Filters',
            'SortCriteria': 0,
            'SortDirection': 0,
            'SearchType': 5,
            'ResultsType': 0,
        }
    )
    return params


SEARCH_PARAMS = _build_search_params()


@register_scraper
class PaloAltoNetworksScraper(RadancyScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.PALO_ALTO_NETWORKS

    @property
    def host(self) -> str:
        return HOST

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def search_params(self) -> dict:
        return SEARCH_PARAMS
