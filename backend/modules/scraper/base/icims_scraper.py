from abc import abstractmethod
from typing import cast

from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.full_list_scraper import FullListScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

DESCRIPTION_FIELDS = ('overview', 'responsibilities', 'qualifications')


class IcimsScraper(FullListScraper):
    """Base for companies whose careers site fronts an iCIMS portal
    (`<tenant>.icims.com/jobs/<id>/<slug>/job`) and publishes a single JSON feed of all
    postings (a bare array of `{id, title, category, locations, portalJobPost.portalUrl,
    overview/responsibilities/qualifications HTML}`, as on Atlassian's careers site).

    The feed has no server-side paging or filters, so it is fetched once, scoped locally
    by category and location keyword, and paged by slicing (see `FullListScraper`).
    Descriptions come straight from the feed; the real public requisition id
    (e.g. `REQ-2026-2256`) only appears on the iCIMS job page's `?in_iframe=1` variant,
    so that page is the detail step."""

    @property
    @abstractmethod
    def job_url_template(self) -> str:
        """Public job URL with a `{job_id}` placeholder."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job."""

    @property
    def allowed_categories(self) -> set[str]:
        """Lowercase feed categories to keep (e.g. {'engineering'}). Empty = all."""
        return set()

    @property
    def location_keywords(self) -> tuple[str, ...]:
        """Lowercase keywords (e.g. ('india', 'remote')); a job is kept if any of its
        locations contains one. Empty = all."""
        return ()

    @property
    def detail_url(self) -> str:
        return ''

    def parse_list_items(self, response_json: dict) -> list[dict]:
        # the feed is a bare JSON array, not an object
        return cast(list[dict], response_json) or []

    def parse_detail_fields(self, response_json: dict) -> dict:
        return {}

    def _in_scope_locations(self, item: dict) -> list[str]:
        # raw values look like "Bengaluru - India -   Bengaluru,  560071 India", "Remote - India - Remote", "Remote - Remote"
        locations = []
        for raw in item.get('locations') or []:
            if self.location_keywords and not any(keyword in raw.lower() for keyword in self.location_keywords):
                continue
            parts = [part.strip() for part in raw.split(' - ')]
            region = parts[1] if len(parts) > 1 and parts[1].lower() != parts[0].lower() else None
            location = f'{parts[0]}, {region}' if region else parts[0]
            if location not in locations:
                locations.append(location)
        return locations

    def include_job(self, item: dict) -> bool:
        if self.allowed_categories and (item.get('category') or '').strip().lower() not in self.allowed_categories:
            return False
        return bool(self._in_scope_locations(item))

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id')
        portal_url = (item.get('portalJobPost') or {}).get('portalUrl')
        if job_id is None or not portal_url:
            self._record_error(None, f'missing id or portalUrl: {item.get("title")}')
            return None

        description_html = ''.join(item.get(field) or '' for field in DESCRIPTION_FIELDS)
        description = BeautifulSoup(description_html, 'html.parser').get_text(separator='\n', strip=True)

        return ScraperJobData(
            url=clean_job_url(self.job_url_template.format(job_id=job_id)),
            official_id=None,
            title=clean_text(item.get('title')),
            company_name=self.company_name,
            location=clean_text('; '.join(self._in_scope_locations(item))),
            description=clean_text(description),
            extra={'portal_url': portal_url},
        )

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.extra['portal_url'], params={'in_iframe': 1})
        response.raise_for_status()
        return self.parse_icims_page(response.text)

    def parse_icims_page(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')

        for label in soup.select('div.header.right span.field-label'):
            if label.get_text(strip=True) == 'ID':
                value = label.find_next_sibling('span')
                official_id = clean_text(value.get_text(strip=True)) if value else None
                return {'official_id': official_id} if official_id else {}

        return {}
