from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

SEARCH_URL = 'https://careers.bankofamerica.com/services/jobssearchservlet'
BASE_URL = 'https://careers.bankofamerica.com'
COMPANY_NAME = 'Bank of America'
PAGE_SIZE = 5000

DEFAULT_SEARCH_FILTERS = {
    'filters': 'area=Technology',
    'sort': 'newest',
    'search': 'jobsByLocation',
    'searchstring': 'India',
}


@register_scraper
class BankOfAmericaScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.BANK_OF_AMERICA

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return SEARCH_URL

    @property
    def detail_url(self) -> str:
        return BASE_URL

    def build_list_params(self, start: int) -> dict:
        return {**DEFAULT_SEARCH_FILTERS, 'start': start, 'rows': PAGE_SIZE}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('jobsList') or []

    def extract_total_count(self, response_json: dict) -> int | None:
        return response_json.get('totalMatches')

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        requisition_id = item.get('jobRequisitionId')
        job_path = item.get('jcrURL')
        if not requisition_id or not job_path:
            self._record_error(None, f'missing jobRequisitionId or jcrURL: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(f'{BASE_URL}{job_path}'),
            official_id=str(requisition_id),
            title=clean_text(item.get('postingTitle')),
            company_name=COMPANY_NAME,
            location=clean_text(item.get('location')),
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.url)
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        description_el = soup.select_one('div.js-job-description-body-internal')
        description = clean_text(description_el.get_text(separator='\n', strip=True)) if description_el else None
        return {'description': description}
