import html
import json
import re
import threading
from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

_TOKEN_PATTERN = re.compile(r'__RequestVerificationToken" type="hidden" value="([^"]+)"')
_PRELOAD_PATTERN = re.compile(r'id="preLoadJSON" type="hidden" value="([^"]*)"')

JOB_REFERENCE_ZONE = 'autoreq'
CITY_ZONE = 'formtext2'
COUNTRY_ZONE = 'formtext23'


class BrassringScraper(ApiScraper):
    """Base for scrapers targeting an IBM/Kenexa BrassRing careers site (`/TGnewUI/Search/...`,
    identifiable by the `TGnewUI` path and `tg_session` cookies). The site has no open API:
    its own XHR endpoints (`Ajax/MatchedJobs` for the list, `Ajax/JobDetails` for a job) need
    a session cookie, a CSRF token (sent as the `RFT` header) and a per-session encrypted
    value, all scraped from the search page's HTML. Every matching job comes back in one
    `MatchedJobs` response when `DocsPerPage` is large enough (`PageNumber` is ignored).
    Subclasses only supply the host, partner/site ids, company name and facet filters."""

    def __init__(self):
        super().__init__()
        self._bootstrap_lock = threading.Lock()
        self._csrf_token: str | None = None
        self._base_request: dict | None = None

    @property
    @abstractmethod
    def host(self) -> str:
        """e.g. 'jobs.ubs.com'."""

    @property
    @abstractmethod
    def partner_id(self) -> str:
        """The `partnerid` query param of the careers site URL."""

    @property
    @abstractmethod
    def site_id(self) -> str:
        """The `siteid` query param of the careers site URL."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'UBS'."""

    @property
    def facet_filters(self) -> dict[str, list[str]]:
        """Search facets to apply as `{facet_name: [option values]}`, e.g.
        `{'formtext2': ['Pune'], 'formtext21': ['Digital']}` - facet names and values
        are listed in the `Facets` of a `MatchedJobs` response. Empty means unfiltered."""
        return {}

    @property
    def excluded_description_labels(self) -> set[str]:
        """Lowercase labels of detail-page text sections to leave out of the description
        (tenant boilerplate such as 'about us' or legal disclaimers)."""
        return set()

    @property
    def page_size(self) -> int:
        return 10000

    @property
    def list_url(self) -> str:
        return f'https://{self.host}/TgNewUI/Search/Ajax/MatchedJobs'

    @property
    def detail_url(self) -> str:
        return f'https://{self.host}/TgNewUI/Search/Ajax/JobDetails'

    def _bootstrap(self) -> dict:
        with self._bootstrap_lock:
            if self._base_request is not None:
                return self._base_request
            response = self._request(
                f'https://{self.host}/TGnewUI/Search/home/HomeWithPreLoad',
                params={'partnerid': self.partner_id, 'siteid': self.site_id, 'PageType': 'searchResults'},
            )
            response.raise_for_status()
            token = _TOKEN_PATTERN.search(response.text)
            preload = _PRELOAD_PATTERN.search(response.text)
            if token is None or preload is None:
                raise ValueError('BrassRing bootstrap page is missing the CSRF token or preload JSON')

            search = json.loads(json.loads(html.unescape(preload.group(1)))['SmartSearchJSONValue'])
            self._base_request = {
                'PartnerId': self.partner_id,
                'SiteId': self.site_id,
                'Keyword': '',
                'Location': '',
                'KeywordCustomSolrFields': search['KeywordCustomSolrFields'],
                'LocationCustomSolrFields': search['LocationCustomSolrFields'],
                'TurnOffHttps': False,
                'Latitude': 0,
                'Longitude': 0,
                'PowerSearchOptions': {'PowerSearchOption': []},
                'encryptedsessionvalue': search['EncryptedSessionValue'],
            }
            self._csrf_token = token.group(1)
            return self._base_request

    def _post(self, url: str, body: dict):
        self._bootstrap()
        response = self._session.post(
            url,
            json=body,
            headers={'RFT': self._csrf_token, 'X-Requested-With': 'XMLHttpRequest'},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response

    def build_list_params(self, _start: int) -> dict:
        base_request = self._bootstrap()
        facets = [
            {'Name': name, 'Options': [{'OptionName': value, 'OptionValue': value, 'Selected': True} for value in values]}
            for name, values in self.facet_filters.items()
        ]
        return {
            **base_request,
            'FacetFilterFields': {'Facet': facets} if facets else None,
            'DocsPerPage': self.page_size,
        }

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        response = self._post(self.list_url, self.build_list_params(start))
        items = self.parse_list_items(self._parse_json(response))

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings, stop=True)

    def parse_list_items(self, response_json: dict) -> list[dict]:
        jobs = []
        for job in (response_json.get('Jobs') or {}).get('Job') or []:
            fields = {q.get('QuestionName'): q.get('Value') for q in job.get('Questions') or []}
            fields['link'] = job.get('Link')
            jobs.append(fields)
        return jobs

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        req_id = item.get('reqid')
        link = item.get('link')
        if not req_id or not link:
            self._record_error(None, f'missing reqid or link: {item}')
            return None

        # reqid is BrassRing's internal id; official_id is the public "Job Reference #"
        # shown on the detail page (see parse_detail_fields).
        return ScraperJobData(
            url=clean_job_url(link),
            title=clean_text(html.unescape(item.get('jobtitle') or '')),
            company_name=self.company_name,
            location=clean_text(item.get(COUNTRY_ZONE)),
            extra={'req_id': req_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {
            'partnerId': self.partner_id,
            'siteId': self.site_id,
            'jobid': listing.extra['req_id'],
            'configMode': '',
            'jobSiteId': self.site_id,
            'turnOffHttps': False,
        }

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._post(self.detail_url, self.build_detail_params(listing))
        return self.parse_detail_fields(self._parse_json(response))

    def parse_detail_fields(self, response_json: dict) -> dict:
        questions = ((response_json.get('ServiceResponse') or {}).get('Jobdetails') or {}).get('JobDetailQuestions') or []

        sections = []
        zones = {}
        for question in questions:
            answer = question.get('AnswerValue')
            zones[question.get('VerityZone')] = answer
            label = (question.get('QuestionName') or '').strip().lower()
            if question.get('QuestionType') == 'textarea' and answer and label not in self.excluded_description_labels:
                sections.append(answer)

        fields = {'description': clean_text('\n\n'.join(sections))}

        reference = zones.get(JOB_REFERENCE_ZONE)
        if reference:
            fields['official_id'] = str(reference).strip()

        city, country = zones.get(CITY_ZONE), zones.get(COUNTRY_ZONE)
        location = ', '.join(part.strip() for part in (city, country) if part and part.strip())
        if location:
            fields['location'] = clean_text(location)

        return fields
