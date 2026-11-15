from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

# PCSX is disabled for this tenant, so the legacy apply/v2 API is used (the `/jobs/{pid}/jobs` variant ignores filters)
LIST_URL = 'https://portal.careers.hsbc.com/api/apply/v2/jobs'
DETAIL_URL_TEMPLATE = 'https://portal.careers.hsbc.com/api/apply/v2/jobs/{position_id}'
JOB_URL_TEMPLATE = 'https://portal.careers.hsbc.com/careers/job/{position_id}'
COMPANY_NAME = 'HSBC'
DOMAIN = 'hsbc.com'
PAGE_SIZE = 10  # fixed server-side, `num` is ignored

DEFAULT_SEARCH_FILTERS = {
    'domain': DOMAIN,
    'location': 'India',
    'department': 'Technology',
}


@register_scraper
class HsbcScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.HSBC

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return LIST_URL

    @property
    def detail_url(self) -> str:
        return DETAIL_URL_TEMPLATE

    def build_list_params(self, start: int) -> dict:
        return {**DEFAULT_SEARCH_FILTERS, 'start': start}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('positions') or []

    def extract_total_count(self, response_json: dict) -> int | None:
        return response_json.get('count')

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        position_id = item.get('id')
        if position_id is None:
            self._record_error(None, f'missing position id: {item}')
            return None
        display_job_id = item.get('display_job_id')

        locations = item.get('locations') or ([item['location']] if item.get('location') else [])

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(position_id=position_id)),
            official_id=str(display_job_id) if display_job_id else None,
            title=clean_text(item.get('name')),
            company_name=COMPANY_NAME,
            location=clean_text('; '.join(locations)) if locations else None,
            extra={'position_id': position_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {'domain': DOMAIN}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(
            DETAIL_URL_TEMPLATE.format(position_id=listing.extra['position_id']),
            params=self.build_detail_params(listing),
        )
        response.raise_for_status()
        return self.parse_detail_fields(self._parse_json(response))

    def parse_detail_fields(self, response_json: dict) -> dict:
        return {'description': clean_text(response_json.get('job_description'))}
