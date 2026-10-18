import html
from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

BOARDS_API_BASE = 'https://boards-api.greenhouse.io/v1/boards'
PAGE_SIZE = 10000


class GreenhouseScraper(ApiScraper):
    """Base for scrapers targeting a company's Greenhouse Job Board
    (`boards-api.greenhouse.io/v1/boards/<board_token>`). Greenhouse is a shared ATS
    vendor - the list/detail endpoint shape and response fields are identical across
    every tenant, only the board token (and display name) differ.

    Verified live against Stripe's board (`stripe`): the list endpoint
    (`GET /v1/boards/<board_token>/jobs`) ignores any `page`/`offset` query param and
    always returns the tenant's *entire* job list in one response - there is no
    server-side pagination or filtering of any kind. So instead of the usual
    offset-driven `build_list_params` + `parse_list_items` round trip per page, this
    base fetches that one list response at most once per run (cached on the instance)
    and slices it locally to satisfy `ApiScraper`'s offset-based paging contract -
    zero extra HTTP calls past the first, every run.

    The single-job detail endpoint (`GET /v1/boards/<board_token>/jobs/<job_id>`)
    takes the job id as a path segment rather than a query param, so
    `_fetch_detail_fields` is overridden the same way `WorkdaySraper`/
    `SmartRecruitersScraper` override it for their own path-templated detail URLs."""

    def __init__(self):
        super().__init__()
        # caches the one full-list response per run so later pages just slice it locally
        self._all_jobs: list[dict] | None = None

    @property
    @abstractmethod
    def board_token(self) -> str:
        """Tenant's Greenhouse job-board token, e.g. 'stripe' - the `<board_token>` in
        `boards-api.greenhouse.io/v1/boards/<board_token>/jobs`."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Stripe'."""

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return f'{BOARDS_API_BASE}/{self.board_token}/jobs'

    @property
    def detail_url_template(self) -> str:
        return self.list_url + '/{job_id}'

    @property
    def detail_url(self) -> str:
        # Unused: the per-job detail URL is templated on each listing's own job id
        # (a path segment, not a query param), so `_fetch_detail_fields` is overridden
        # below instead of relying on `build_detail_params` against a fixed URL.
        return self.detail_url_template

    def build_list_params(self, _start: int) -> dict:
        # The list endpoint has no pagination or filter params at all - verified live
        # (a `page` param is silently ignored, always returns every job).
        return {}

    def build_detail_params(self, _listing: ScraperJobData) -> dict:
        return {}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('jobs') or []

    def _fetch_all_jobs(self) -> list[dict]:
        if self._all_jobs is None:
            response = self._request(self.list_url)
            response.raise_for_status()
            self._all_jobs = self.parse_list_items(self._parse_json(response))
        return self._all_jobs

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        all_jobs = self._fetch_all_jobs()
        items = all_jobs[start : start + self.page_size]

        if not items:
            return ListingPage(stop=True)

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings, stop=start + len(items) >= len(all_jobs))

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id')
        absolute_url = item.get('absolute_url')
        if job_id is None or not absolute_url:
            self._record_error(None, f'missing job id or absolute_url: {item}')
            return None

        location = (item.get('location') or {}).get('name')

        return ScraperJobData(
            url=clean_job_url(absolute_url),
            official_id=None,
            title=clean_text(item.get('title')),
            company_name=self.company_name,
            location=clean_text(location),
            extra={'job_id': job_id},
        )

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(self.detail_url_template.format(job_id=listing.extra['job_id']))
        response.raise_for_status()
        return self.parse_detail_fields(self._parse_json(response))

    def parse_detail_fields(self, response_json: dict) -> dict:
        # Greenhouse's `content` field is HTML that has itself been HTML-escaped once
        # (e.g. literal "&lt;h2&gt;" rather than "<h2>") - verified live against
        # Stripe's job detail responses - so it needs one `html.unescape` pass to turn
        # the entities back into real tags before `clean_text` strips them and
        # unescapes whatever's left.
        content = response_json.get('content')
        description = html.unescape(content) if content else None
        return {'description': clean_text(description)}
