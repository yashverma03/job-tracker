from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

BASE_URL = 'https://www.amazon.jobs'
LIST_URL = f'{BASE_URL}/en/search.json'
COMPANY_NAME = 'Amazon'
# Server-side ceiling: larger `result_limit` values return no jobs
PAGE_SIZE = 100

DEFAULT_SEARCH_FILTERS = {
    'category[]': 'software-development',
    'normalized_country_code[]': 'IND',
    'industry_experience[]': 'one_to_three_years',
    'is_manager[]': '0',
    'sort': 'relevant',
    'base_query': 'software',
    'loc_query': 'India',
    'country': 'IND',
}
DESCRIPTION_FIELDS = ('description', 'basic_qualifications', 'preferred_qualifications')


@register_scraper
class AmazonScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.AMAZON

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return LIST_URL

    @property
    def detail_url(self) -> str:
        # Unused: the list response already carries the full description.
        return LIST_URL

    def build_list_params(self, start: int) -> dict:
        return {**DEFAULT_SEARCH_FILTERS, 'offset': start, 'result_limit': self.page_size}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('jobs') or []

    def extract_total_count(self, response_json: dict) -> int | None:
        return response_json.get('hits')

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id_icims')
        job_path = item.get('job_path')
        if not job_id or not job_path:
            self._record_error(None, f'missing id_icims or job_path: {item}')
            return None

        description = '<br/><br/>'.join(item[field] for field in DESCRIPTION_FIELDS if item.get(field))

        return ScraperJobData(
            url=clean_job_url(f'{BASE_URL}{job_path}'),
            official_id=str(job_id),
            title=clean_text(item.get('title')),
            company_name=COMPANY_NAME,
            location=clean_text(item.get('normalized_location') or item.get('location')),
            description=clean_text(description),
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        return {}

    def parse_detail_fields(self, response_json: dict) -> dict:
        return {}
