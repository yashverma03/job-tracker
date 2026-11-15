import json

from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

BASE_URL = 'https://careers.servicenow.com'
LIST_URL = f'{BASE_URL}/jobs/'
COMPANY_NAME = 'ServiceNow'
# Server-side ceiling: any larger `pagesize` still returns 50 results per page.
PAGE_SIZE = 50

SEARCH_PARAMS = {
    'team': ['Digital Technology', 'Engineering, Infrastructure and Operations', 'IT'],
    'country': 'India',
}


@register_scraper
class ServiceNowScraper(ApiScraper):
    """ServiceNow's careers site has no JSON API - both the list (`/jobs/`, filters and
    `page` as query params) and the detail page are server-rendered HTML."""

    @property
    def name(self) -> ScraperName:
        return ScraperName.SERVICENOW

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return LIST_URL

    @property
    def detail_url(self) -> str:
        # Unused: detail is fetched from each listing's own URL, see `_fetch_detail_fields`.
        return LIST_URL

    def build_list_params(self, start: int) -> dict:
        return {**SEARCH_PARAMS, 'pagesize': self.page_size, 'page': start // self.page_size + 1}

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        response = self._request(self.list_url, params=self.build_list_params(start))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        items = self.parse_list_items(soup)

        if not items:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        total = self.extract_total_count(soup)
        return ListingPage(listings=listings, stop=isinstance(total, int) and start + len(items) >= total)

    def extract_total_count(self, soup: BeautifulSoup) -> int | None:
        results = soup.select_one('#js-job-search-results')
        value = results.get('data-results') if results else None
        return int(value) if value and value.isdigit() else None

    def parse_list_items(self, soup: BeautifulSoup) -> list[dict]:
        # Scoped to the results grid - the page also renders unrelated promo job cards outside it
        items = []
        for card in soup.select('#js-job-search-results .card-job'):
            link = card.select_one('h2.card-title a')
            if link is None:
                continue
            location_el = card.select_one('.job-meta li')
            items.append(
                {
                    'href': link.get('href'),
                    'title': link.get_text(' ', strip=True),
                    'location': location_el.get_text(' ', strip=True) if location_el else None,
                }
            )
        return items

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        href = item.get('href')
        if not href:
            self._record_error(None, f'missing job link: {item}')
            return None

        # The URL's numeric id is ServiceNow's internal id; official_id comes from the
        # detail page's JobPosting identifier (see parse_detail_fields).
        return ScraperJobData(
            url=clean_job_url(f'{BASE_URL}{href}' if href.startswith('/') else href),
            title=clean_text(item.get('title')),
            company_name=COMPANY_NAME,
            location=clean_text(item.get('location')),
        )

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.url)
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
            except (TypeError, ValueError):
                continue
            if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                fields = {'description': clean_text(data.get('description'))}
                identifier = data.get('identifier')
                if identifier:
                    fields['official_id'] = str(identifier).strip()
                return fields

        return {'description': None}
