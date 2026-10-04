from abc import abstractmethod

from common.utils.http import post_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text


class WorkdayScraper(ApiScraper):
    """Base for scrapers targeting a Workday-hosted careers site (`*.myworkdayjobs.com`).
    Many companies (Adobe included) run their external career site on Workday, sharing
    the same list/detail API shape - only the host, tenant, site and search facets
    differ. Subclasses only need to implement the properties below and
    `map_item_to_listing`; pagination and the POST-based list request are handled
    here."""

    @property
    @abstractmethod
    def workday_host(self) -> str:
        """e.g. 'adobe.wd5.myworkdayjobs.com'."""

    @property
    @abstractmethod
    def tenant(self) -> str:
        """e.g. 'adobe'."""

    @property
    @abstractmethod
    def site(self) -> str:
        """e.g. 'external_experienced'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Adobe'."""

    @property
    def applied_facets(self) -> dict:
        """Workday search facets (job family, location, employment type, etc.) as
        `{facetParameter: [id, ...]}`. Override to scope the search per company."""
        return {}

    @property
    def search_text(self) -> str:
        return ''

    @property
    def page_size(self) -> int:
        return 20

    @property
    def list_url(self) -> str:
        return f'https://{self.workday_host}/wday/cxs/{self.tenant}/{self.site}/jobs'

    @property
    def detail_base_url(self) -> str:
        return f'https://{self.workday_host}/wday/cxs/{self.tenant}/{self.site}'

    @property
    def job_url_base(self) -> str:
        return f'https://{self.workday_host}/{self.site}'

    @property
    def detail_url(self) -> str:
        # Unused: `_fetch_detail_fields` is overridden below since the per-job detail
        # URL is built from each listing's own external path, not a fixed endpoint.
        return self.detail_base_url

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def build_list_params(self, start: int) -> dict:
        return {
            'appliedFacets': self.applied_facets,
            'searchText': self.search_text,
            'limit': self.page_size,
            'offset': start,
        }

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('jobPostings', [])

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        external_path = item.get('externalPath')
        bullet_fields = item.get('bulletFields') or []
        official_id = bullet_fields[0] if bullet_fields else None
        if not external_path or not official_id:
            self._record_error(None, f'missing externalPath or bulletFields: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(self.job_url_base + external_path),
            official_id=official_id,
            title=clean_text(item.get('title')),
            company_name=self.company_name,
            extra={'external_path': external_path},
        )

    def parse_detail_fields(self, response_json: dict) -> dict:
        posting_info = response_json.get('jobPostingInfo', {})
        locations = [posting_info.get('location'), *(posting_info.get('additionalLocations') or [])]
        location_text = ', '.join(location for location in locations if location)

        return {
            'description': clean_text(posting_info.get('jobDescription')),
            'location': clean_text(location_text) if location_text else None,
        }

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        response = post_with_retry(
            lambda: self._session,
            self.list_url,
            json=self.build_list_params(start),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_json = self._parse_json(response)
        items = self.parse_list_items(response_json)

        if not items:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        # Once `start` passes the real result count, Workday re-serves the last page
        # instead of an empty one, which would otherwise page forever. `total` in the
        # response is authoritative, so stop as soon as this page reaches/passes it.
        total = response_json.get('total')
        stop = isinstance(total, int) and start + len(items) >= total
        if stop:
            self._logger.info('stopping pagination, reached total=%s at start=%s', total, start)

        return ListingPage(listings=listings, stop=stop)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(self.detail_base_url + listing.extra['external_path'])
        response.raise_for_status()
        return self.parse_detail_fields(self._parse_json(response))
