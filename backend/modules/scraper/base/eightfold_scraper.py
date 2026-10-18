from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

PAGE_SIZE = 10
JOB_URL_TEMPLATE = 'https://app.eightfold.ai/careers/job/{position_id}'
SEARCH_URL = 'https://app.eightfold.ai/api/pcsx/search'
DETAIL_URL = 'https://app.eightfold.ai/api/pcsx/position_details'


class EightfoldScraper(ApiScraper):
    """Base for scrapers targeting a company's careers site hosted on Eightfold AI
    (`app.eightfold.ai`) - a shared vendor talent/ATS platform many companies run
    their external careers page on unmodified. Every tenant shares the same
    `/api/pcsx/search` (list) and `/api/pcsx/position_details` (detail) endpoints,
    request/response shape, and pagination (a `start` offset, fixed 10-item page size
    not controllable via a `num`/limit param - verified live), differing only by a
    `domain=` tenant param and this tenant's own department/seniority/location search
    facet values.

    Verified live against the `domain=eightfold.ai` tenant: the list endpoint's
    `data.count` field is the true total-match count (constant across pages, confirmed
    by paging to its boundary), so pagination stops there rather than waiting for an
    empty page. List items only expose a single numeric id (`id` / `displayJobId` /
    `atsJobId` - always identical, confirmed across list and detail responses for
    several jobs), with no separate human-facing requisition/reference id anywhere in
    either payload, so that numeric id is used directly as `official_id` (not a
    fallback - its exclusivity was explicitly confirmed, not assumed)."""

    @property
    @abstractmethod
    def domain(self) -> str:
        """Tenant identifier for this company's Eightfold-hosted careers site, e.g.
        'eightfold.ai' - the `domain=` query param value."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Eightfold AI'."""

    @property
    def location(self) -> str:
        return 'India'

    @property
    def include_remote(self) -> bool:
        return True

    @property
    def departments(self) -> list[str]:
        """`filter_department` facet value(s) - verified live to narrow results
        (e.g. 'Engineering'). Override per tenant; empty means unfiltered."""
        return []

    @property
    def seniority_levels(self) -> list[str]:
        """`filter_seniority` facet value(s) - verified live via this tenant's own
        `filterDef.smartFilters` options (e.g. '1'=Entry, '2'=Mid/Senior, '4'=VP).
        Override per tenant since the numeric ids aren't guaranteed stable across
        tenants; empty means unfiltered."""
        return []

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return SEARCH_URL

    @property
    def detail_url(self) -> str:
        return DETAIL_URL

    def build_list_params(self, start: int) -> dict:
        params = {
            'domain': self.domain,
            'query': '',
            'location': self.location,
            'start': start,
            'sort_by': 'timestamp',
            'filter_include_remote': '1' if self.include_remote else '0',
        }
        if self.departments:
            params['filter_department'] = list(self.departments)
        if self.seniority_levels:
            params['filter_seniority'] = list(self.seniority_levels)
        return params

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('data', {}).get('positions', [])

    def extract_total_count(self, response_json: dict) -> int | None:
        return response_json.get('data', {}).get('count')

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        position_id = item.get('id') or item.get('displayJobId')
        if position_id is None:
            self._record_error(None, f'missing position id: {item}')
            return None

        locations = item.get('locations') or item.get('standardizedLocations') or []

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(position_id=position_id)),
            official_id=str(position_id),
            title=clean_text(item.get('name')),
            company_name=self.company_name,
            location=clean_text('; '.join(locations)) if locations else None,
            extra={'position_id': position_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {'position_id': listing.extra['position_id'], 'domain': self.domain, 'hl': 'en'}

    def parse_detail_fields(self, response_json: dict) -> dict:
        description = response_json.get('data', {}).get('jobDescription')
        return {'description': clean_text(description)}
