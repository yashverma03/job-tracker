import re
from abc import abstractmethod

from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

AVATURE_PAGE_SIZE = 12
# Matches the result legend's aria-label, e.g. "334 results" or "1 result".
_RESULT_COUNT_PATTERN =re.compile(r'(\d+)\s+results?', re.IGNORECASE)


class AvatureScraper(ApiScraper):
    """Base for scrapers targeting an Avature-hosted careers site (`*.avature.net`, or a
    custom domain serving Avature's `/careers/SearchJobs` + `/careers/JobDetail` pages;
    identifiable by `avacdn.net` references in the page's CSP header). Avature exposes no
    JSON API for its public careers site, so the list page (`SearchJobs`, filters and
    paging as query params) and the detail page (`JobDetail/<slug>/<id>`) are both
    server-rendered HTML. All fetching/parsing lives here - subclasses only supply the
    host, company name, and this company's fixed search filter params."""

    @property
    @abstractmethod
    def host(self) -> str:
        """e.g. 'bloomberg.avature.net'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Bloomberg'."""

    @property
    @abstractmethod
    def search_params(self) -> dict:
        """This company's fixed search filter query params, exactly as the site's own
        search UI puts them in the URL (e.g. `{'1845': '[162477,162575]',
        '1845_format': 3996, 'listFilterMode': 1}`) - everything except
        `jobRecordsPerPage`/`jobOffset`, which are filled in per page below."""

    @property
    def careers_path(self) -> str:
        """Path prefix the site's SearchJobs/JobDetail pages live under."""
        return '/careers'

    @property
    def official_id_label(self) -> str:
        """Label of the detail-page field holding the job's public reference id."""
        return 'Ref #'

    @property
    def page_size(self) -> int:
        # The site always serves 12 results per page and ignores `jobRecordsPerPage`
        # (verified with values from 5 to 1000), so this is the real ceiling.
        return AVATURE_PAGE_SIZE

    @property
    def list_url(self) -> str:
        return f'https://{self.host}{self.careers_path}/SearchJobs/'

    @property
    def detail_url(self) -> str:
        # Unused: detail is fetched from each listing's own URL, see `_fetch_detail_fields`.
        return f'https://{self.host}{self.careers_path}/JobDetail/'

    def build_list_params(self, start: int) -> dict:
        params = dict(self.search_params)
        params.update({'jobRecordsPerPage': self.page_size, 'jobOffset': start})
        return params

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        response = self._request(self.list_url, params=self.build_list_params(start))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        items = self.parse_list_items(soup)

        # Past the last page the site renders a single "No jobs found" card (no detail
        # link), which parse_list_items skips, so an empty result means the end.
        if not items:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        total = self.extract_total_count(soup)
        stop = isinstance(total, int) and start + len(items) >= total
        return ListingPage(listings=listings, stop=stop)

    def extract_total_count(self, soup: BeautifulSoup) -> int | None:
        legend = soup.select_one('.list-controls__text__legend')
        match = _RESULT_COUNT_PATTERN.search(legend.get('aria-label') or '') if legend else None
        return int(match.group(1)) if match else None

    def parse_list_items(self, soup: BeautifulSoup) -> list[dict]:
        items = []
        for card in soup.select('article.article--result'):
            link = card.select_one('a[href*="/JobDetail/"]')
            if link is None:
                continue
            location_el = card.select_one('.list-item-location')
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

        # The id in the URL is Avature's internal posting id, not the public reference
        # id - official_id comes from the detail page (see parse_detail_fields).
        return ScraperJobData(
            url=clean_job_url(f'https://{self.host}{href}' if href.startswith('/') else href),
            title=clean_text(item.get('title')),
            company_name=self.company_name,
            location=clean_text(item.get('location')),
        )

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.url)
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        fields = {}

        official_id = self._find_labelled_value(soup, self.official_id_label)
        if official_id:
            fields['official_id'] = official_id

        description_blocks = soup.select('article.article--details .field--rich-text')
        description = '\n'.join(block.get_text('\n', strip=True) for block in description_blocks)
        fields['description'] = clean_text(description) if description else None
        return fields

    @staticmethod
    def _find_labelled_value(soup: BeautifulSoup, label: str) -> str | None:
        for field in soup.select('.article__content__view__field'):
            label_el = field.select_one('.article__content__view__field__label')
            value_el = field.select_one('.article__content__view__field__value')
            if label_el and value_el and label_el.get_text(strip=True) == label:
                return value_el.get_text(strip=True) or None
        return None
