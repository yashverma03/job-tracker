import json
from abc import abstractmethod
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common.utils.http import get_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.http_session import new_session
from modules.scraper.utils.nextjs_rsc import extract_json_value, fetch_rsc_payload
from modules.scraper.utils.text_cleaner import clean_text

PAGE_SIZE = 12


class HappydanceScraper(BaseScraper):
    """Base for scrapers targeting a Happydance-hosted careers site
    (`jobs.<company>.com`, powered by the happydance.love vendor platform). List
    pagination, RSC-payload parsing, and JSON-LD detail parsing are identical across
    every tenant - subclasses only configure the host, display name, and search
    scoping."""

    def __init__(self):
        super().__init__()
        self._session = new_session()

    @property
    @abstractmethod
    def host(self) -> str:
        """Tenant's Happydance-hosted domain, e.g. 'jobs.sap.com'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'SAP'."""

    @property
    def search_params(self) -> dict:
        """Extra query params scoping the listing search (e.g. `team`/`country` facet
        values) sent as-is on every list page request, in addition to `page`. Empty by
        default - override per tenant. A list value is sent as a repeated query param
        (OR semantics), matching how the site's own search UI builds its URL."""
        return {}

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return f'https://{self.host}/en/jobs/'

    def _request(self, url: str, **kwargs):
        kwargs.setdefault('timeout', REQUEST_TIMEOUT_SECONDS)
        return get_with_retry(lambda: self._session, url, **kwargs)

    def _extract_job_listing(self, payload: str) -> tuple[list[dict], dict]:
        """Pulls the `jobs` array and pagination metadata (totalPages/totalJobs/
        currentPage/pageSize) out of the page's RSC payload - each pulled
        independently via `extract_json_value` (not a combined regex), since they're
        just scalar fields on the same object and the order/exact surrounding
        punctuation isn't a format guarantee."""
        jobs, jobs_end = extract_json_value(payload, 'jobs', expected_type=list)
        if jobs is None:
            return [], {}

        pagination = {}
        for key, result_key in (
            ('totalPages', 'total_pages'),
            ('totalJobs', 'total_jobs'),
            ('currentPage', 'current_page'),
            ('pageSize', 'page_size'),
        ):
            value, _ = extract_json_value(payload, key, start=jobs_end)
            if value is not None:
                pagination[result_key] = value
        return jobs, pagination

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        page_number = start // self.page_size + 1
        payload = fetch_rsc_payload(
            lambda: self._session,
            self.list_url,
            params={**self.search_params, 'page': page_number},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        jobs, pagination = self._extract_job_listing(payload)
        if not jobs:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        listings = []
        for job in jobs:
            listing = self.map_item_to_listing(job)
            if listing is not None:
                listings.append(listing)

        total_jobs = pagination.get('total_jobs')
        stop = isinstance(total_jobs, int) and start + len(jobs) >= total_jobs
        if stop:
            self._logger.info('stopping pagination, reached total_jobs=%s at start=%s', total_jobs, start)

        return ListingPage(listings=listings, stop=stop)

    def map_item_to_listing(self, job: dict) -> ScraperJobData | None:
        job_id = job.get('id')
        relative_url = job.get('url')
        if not job_id or not relative_url:
            self._record_error(None, f'missing id or url: {job}')
            return None

        return ScraperJobData(
            url=clean_job_url(urljoin(f'https://{self.host}', relative_url)),
            official_id=str(job_id),
            title=clean_text(job.get('title')),
            company_name=self.company_name,
            location=clean_text(job.get('locations')),
        )

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.url)
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        """Pulls the schema.org `JobPosting` JSON-LD block out of the detail page for
        the only field the listing page doesn't already provide: the full
        description. Overridable in case a tenant's JSON-LD is shaped differently."""
        job_posting = self._find_job_posting_ld_json(html)
        if job_posting is None:
            return {}
        return {'description': clean_text(job_posting.get('description'))}

    def _find_job_posting_ld_json(self, html: str) -> dict | None:
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
            except (TypeError, json.JSONDecodeError):
                continue
            if data.get('@type') == 'JobPosting':
                return data
        return None
