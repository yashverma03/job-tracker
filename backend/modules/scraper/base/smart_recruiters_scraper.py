from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

LIST_URL = 'https://api.smartrecruiters.com/v1/companies/{identifier}/postings'
DETAIL_URL_TEMPLATE = 'https://api.smartrecruiters.com/v1/companies/{identifier}/postings/{posting_id}'
JOB_URL_TEMPLATE = 'https://jobs.smartrecruiters.com/{identifier}/{posting_id}'
PAGE_SIZE = 100

DESCRIPTION_SECTIONS = ('jobDescription', 'qualifications', 'additionalInformation', 'companyDescription')


class SmartRecruitersScraper(ApiScraper):
    """Base for scrapers targeting a company's SmartRecruiters-hosted careers site
    (`jobs.smartrecruiters.com/<identifier>/...`). SmartRecruiters is a shared ATS
    vendor with a public JSON API - list/detail shape, pagination, and field layout
    are identical across tenants; only the company identifier and search-scoping
    query params differ. Subclasses only need to implement the properties below."""

    @property
    @abstractmethod
    def company_identifier(self) -> str:
        """The tenant's SmartRecruiters company identifier, e.g. 'PHONEPELIMITED'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'PhonePe'."""

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def search_params(self) -> dict:
        """This company's fixed search query params (e.g. `q` for a keyword query,
        `country`) - everything except `limit`/`offset`, which are filled in per-page
        below. Empty by default since SmartRecruiters' own facet filters (department,
        function, etc.) aren't exposed as stable query params the way `q`/`country`
        are - override to scope the search further per company."""
        return {}

    @property
    def list_url(self) -> str:
        return LIST_URL.format(identifier=self.company_identifier)

    @property
    def detail_url_template(self) -> str:
        return DETAIL_URL_TEMPLATE.format(identifier=self.company_identifier, posting_id='{posting_id}')

    @property
    def detail_url(self) -> str:
        # Unused: `_fetch_detail_fields` is overridden below since the detail URL is
        # templated on each listing's own posting id, not a fixed endpoint.
        return self.detail_url_template

    def build_list_params(self, start: int) -> dict:
        return {**self.search_params, 'limit': self.page_size, 'offset': start}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('content') or []

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        posting_id = item.get('id')
        if not posting_id:
            self._record_error(None, f'missing posting id: {item}')
            return None

        location = item.get('location') or {}

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(identifier=self.company_identifier, posting_id=posting_id)),
            title=clean_text(item.get('name')),
            company_name=self.company_name,
            location=clean_text(location.get('fullLocation')),
            extra={'posting_id': posting_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(self.detail_url_template.format(posting_id=listing.extra['posting_id']))
        response.raise_for_status()
        return self.parse_detail_fields(self._parse_json(response))

    def parse_detail_fields(self, response_json: dict) -> dict:
        sections = (response_json.get('jobAd') or {}).get('sections') or {}
        description = '\n\n'.join(
            text for text in (sections.get(name, {}).get('text') for name in DESCRIPTION_SECTIONS) if text
        )
        location = response_json.get('location') or {}

        return {
            'description': clean_text(description),
            'location': clean_text(location.get('fullLocation')),
        }
