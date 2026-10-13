import json
from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text


class RippleHireScraper(ApiScraper):
    """Base for scrapers targeting a RippleHire-hosted careers site
    (`<tenant>.ripplehire.com`). RippleHire is a shared multi-tenant ATS vendor (Paytm,
    LTIMindtree and Axis Bank are all public RippleHire customers) - the list/detail
    endpoint pair (`candidatejobsearch` + `candidatejobdetail`), keyed by a per-tenant
    `token` and `acc` (account) name, is identical across tenants; only the host, token,
    account name and search-scoping params differ. Subclasses only need to implement the
    properties below.

    Both endpoints serve XML by default, but return plain JSON instead when sent an
    `Accept: application/json` + `X-Requested-With: XMLHttpRequest` header pair
    (verified live) - set on the session below - so this otherwise behaves like a
    standard `ApiScraper`."""

    def __init__(self):
        super().__init__()
        self._session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self._session.headers['X-Requested-With'] = 'XMLHttpRequest'

    @property
    @abstractmethod
    def ripplehire_host(self) -> str:
        """e.g. 'paytm.ripplehire.com'."""

    @property
    @abstractmethod
    def token(self) -> str:
        """Per-tenant career-site token, found in the site's own URL query string."""

    @property
    @abstractmethod
    def account(self) -> str:
        """RippleHire's `acc` (account/company) identifier, e.g. 'Paytm'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Paytm'."""

    @property
    @abstractmethod
    def search(self) -> str:
        """Keyword for RippleHire's `search` param. Verified live: an empty value
        returns zero results, so this is mandatory, not optional scoping."""

    @property
    def search_params(self) -> dict:
        """Extra params merged into every list request on top of the fixed ones
        `build_list_params` always sends (`page`, `search`, `token`, `source`,
        `pagesize`, `acc`, `location`, `function`) - e.g. `exp` (a years-of-experience
        band; verified live that RippleHire keeps a job only when
        `jobMinExp <= exp <= jobMaxExp`) to scope by seniority, or overriding
        `location`/`function` to scope by city/department. Empty by default."""
        return {}

    @property
    def page_size(self) -> int:
        return 10000

    @property
    def list_url(self) -> str:
        return f'https://{self.ripplehire_host}/candidate/candidatejobsearch'

    @property
    def detail_url(self) -> str:
        return f'https://{self.ripplehire_host}/candidate/candidatejobdetail'

    @property
    def job_url_base(self) -> str:
        return f'https://{self.ripplehire_host}/candidate/?token={self.token}&lang=en&source=CAREERSITE'

    @property
    def list_http_method(self) -> str:
        return 'POST'

    @property
    def post_body_format(self) -> str:
        return 'form'

    def build_list_params(self, start: int) -> dict:
        query = {
            'page': start // self.page_size,
            'search': self.search,
            'token': self.token,
            'source': 'CAREERSITE',
            'pagesize': self.page_size,
            'acc': self.account,
            'location': '',
            'function': '',
            **self.search_params,
        }
        return {'careerSiteUrlParams': json.dumps(query), 'lang': 'en'}

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {
            'token': self.token,
            'jobSeq': listing.official_id,
            'source': 'CAREERSITE',
            'lang': 'en',
        }

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('jobVoList') or []

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_seq = item.get('jobSeq')
        if not job_seq:
            self._record_error(None, f'missing jobSeq: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(f'{self.job_url_base}#detail/job/{job_seq}'),
            official_id=job_seq,
            title=clean_text(item.get('jobTitle')),
            company_name=self.company_name,
            location=clean_text(item.get('locations')),
        )

    def parse_detail_fields(self, response_json: dict) -> dict:
        job = response_json.get('jobVO') or {}
        return {'description': clean_text(job.get('jobDesc'))}
