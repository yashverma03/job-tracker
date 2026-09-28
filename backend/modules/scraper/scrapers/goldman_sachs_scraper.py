from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

GRAPHQL_URL = 'https://api-higher.gs.com/gateway/api/v1/graphql'
JOB_URL_TEMPLATE = 'https://higher.gs.com/roles/{source_id}'
COMPANY_NAME = 'Goldman Sachs'
PAGE_SIZE = 20

LIST_QUERY = """
query GetRoles($searchQueryInput: RoleSearchQueryInput!) {
  roleSearch(searchQueryInput: $searchQueryInput) {
    totalCount
    items {
      roleId
      corporateTitle
      jobTitle
      jobFunction
      locations {
        primary
        state
        country
        city
        __typename
      }
      status
      division
      externalSource {
        sourceId
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

DETAIL_QUERY = """
query GetRoleById($externalSourceId: String!, $externalSourceFetch: Boolean) {
  role(
    externalSourceId: $externalSourceId
    externalSourceFetch: $externalSourceFetch
  ) {
    roleId
    jobTitle
    descriptionHtml
    __typename
  }
}
"""

SEARCH_FILTERS = [
    {
        'filterCategoryType': 'EXPERIENCE_LEVEL',
        'filters': [{'filter': 'Analyst', 'subFilters': []}],
    },
    {
        'filterCategoryType': 'JOB_FUNCTION',
        'filters': [{'filter': 'Software Engineering', 'subFilters': []}],
    },
    {
        'filterCategoryType': 'LOCATION',
        'filters': [
            {
                'filter': 'India',
                'subFilters': [
                    {
                        'filter': 'Karnataka',
                        'subFilters': [{'filter': 'Bengaluru', 'subFilters': []}],
                    },
                    {
                        'filter': 'Maharashtra',
                        'subFilters': [{'filter': 'Mumbai', 'subFilters': []}],
                    },
                    {
                        'filter': 'Telangana',
                        'subFilters': [{'filter': 'Hyderabad', 'subFilters': []}],
                    },
                ],
            }
        ],
    },
]


@register_scraper
class GoldmanSachsScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.GOLDMAN_SACHS

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return GRAPHQL_URL

    @property
    def detail_url(self) -> str:
        return GRAPHQL_URL

    def build_list_params(self, start: int) -> dict:
        return {
            'operationName': 'GetRoles',
            'query': LIST_QUERY,
            'variables': {
                'searchQueryInput': {
                    'page': {'pageSize': self.page_size, 'pageNumber': start // self.page_size},
                    'sort': {'sortStrategy': 'POSTED_DATE', 'sortOrder': 'DESC'},
                    'filters': SEARCH_FILTERS,
                    'experiences': ['EARLY_CAREER', 'PROFESSIONAL'],
                    'searchTerm': '',
                }
            },
        }

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('data', {}).get('roleSearch', {}).get('items', [])

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        source_id = (item.get('externalSource') or {}).get('sourceId')
        if not source_id:
            self._record_error(None, f'missing externalSource.sourceId: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(source_id=source_id)),
            official_id=str(source_id),
            title=clean_text(item.get('corporateTitle')),
            company_name=COMPANY_NAME,
            location=clean_text(_build_location_text(item.get('locations') or [])),
            extra={'source_id': source_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {
            'operationName': 'GetRoleById',
            'query': DETAIL_QUERY,
            'variables': {
                'externalSourceId': str(listing.extra['source_id']),
                'externalSourceFetch': True,
            },
        }

    def parse_detail_fields(self, response_json: dict) -> dict:
        description = response_json.get('data', {}).get('role', {}).get('descriptionHtml')
        return {'description': clean_text(description)}

    @property
    def list_http_method(self) -> str:
        return 'POST'

    @property
    def detail_http_method(self) -> str:
        return 'POST'


def _build_location_text(locations: list[dict]) -> str | None:
    if not locations:
        return None

    primary = next((location for location in locations if location.get('primary')), locations[0])
    parts = [primary.get('city'), primary.get('state')]
    return ', '.join(part for part in parts if part)
