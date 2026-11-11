import html
from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.full_list_scraper import FullListScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

BOARDS_API_BASE = 'https://boards-api.greenhouse.io/v1/boards'


class GreenhouseScraper(FullListScraper):
    """Base for a company's Greenhouse Job Board (`boards-api.greenhouse.io/v1/boards/<board_token>`).
    The shape is identical across tenants, so subclasses only set the board token, company name
    and optional `allowed_countries` / `allowed_departments`. The list endpoint can't be paged or
    filtered server-side (see `FullListScraper`); the detail endpoint takes the job id as a path
    segment, hence the `_fetch_detail_fields` override."""

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
    def list_url(self) -> str:
        return f'{BOARDS_API_BASE}/{self.board_token}/jobs'

    @property
    def allowed_countries(self) -> set[str]:
        """Lowercase country names a job's location or offices must contain. Empty = no filter."""
        return set()

    @property
    def allowed_departments(self) -> set[str]:
        """Lowercase department names a job must belong to (exact match). Empty = no filter."""
        return set()

    @property
    def list_query_params(self) -> dict:
        # `departments`/`offices` are only present on list items when `content=true`
        if self.allowed_countries or self.allowed_departments:
            return {'content': 'true'}
        return {}

    @property
    def detail_url_template(self) -> str:
        return self.list_url + '/{job_id}'

    @property
    def detail_url(self) -> str:
        return self.detail_url_template

    def include_job(self, item: dict) -> bool:
        if self.allowed_countries:
            place_names = [
                (item.get('location') or {}).get('name'),
                *(office.get('name') for office in item.get('offices') or []),
            ]
            if not any(
                country in (name or '').lower() for name in place_names for country in self.allowed_countries
            ):
                return False

        if self.allowed_departments:
            department_names = {(d.get('name') or '').strip().lower() for d in item.get('departments') or []}
            if not department_names & self.allowed_departments:
                return False

        return True

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('jobs') or []

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
        # `content` is HTML-escaped once, so it needs an unescape before tags are stripped
        content = response_json.get('content')
        description = html.unescape(content) if content else None
        return {'description': clean_text(description)}
