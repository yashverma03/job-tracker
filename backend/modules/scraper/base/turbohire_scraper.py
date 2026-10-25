import json
import time
from abc import abstractmethod

from common.utils.http import get_with_retry, post_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

API_BASE_URL = 'https://thapi.azurewebsites.net'
TOKEN_URL = f'{API_BASE_URL}/api/token/noauth'
LIST_URL = f'{API_BASE_URL}/api/careerpagev2/filteredjobs'
TOKEN_EXPIRY_MARGIN_SECONDS = 60
UNFILTERED = {'Value': None, 'FilterType': 0}


class TurbohireScraper(ApiScraper):
    """Base for scrapers targeting a company's TurboHire-hosted careers site
    (`<company>.turbohire.co`), a shared vendor ATS. Every tenant uses the same
    `thapi.azurewebsites.net` API: a public bearer token from `/api/token/noauth`
    (rejected unless the request carries the careers site as `Referer`, as the page's
    own browser does), then one POST to `careerpagev2/filteredjobs` that returns every
    matching job at once - no pagination, and each item already carries the full
    description, so there is no separate detail request. Subclasses only configure the
    careers host and org id."""

    @property
    @abstractmethod
    def host(self) -> str:
        """Tenant's careers site host, e.g. 'flipkart.turbohire.co'."""

    @property
    @abstractmethod
    def org_id(self) -> str:
        """The tenant's `orgId` (a GUID, from the careers page URL)."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Flipkart'."""

    @property
    def keyword(self) -> str:
        return ''

    @property
    def page_size(self) -> int:
        # The API returns everything in one response; this only advances the run loop's offset.
        return 1000

    @property
    def list_url(self) -> str:
        return LIST_URL

    @property
    def detail_url(self) -> str:
        # Unused: descriptions come with the list items.
        return LIST_URL

    @property
    def _referer_headers(self) -> dict:
        return {'Referer': f'https://{self.host}/'}

    def _get_access_token(self) -> str:
        token = getattr(self, '_access_token', None)
        if token and time.monotonic() < self._access_token_expires_at:
            return token

        response = get_with_retry(
            lambda: self._session, TOKEN_URL, headers=self._referer_headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        payload = self._parse_json(response)
        self._access_token = payload['access_token']
        self._access_token_expires_at = (
            time.monotonic() + payload.get('expires_in', 0) - TOKEN_EXPIRY_MARGIN_SECONDS
        )
        return self._access_token

    def build_list_params(self, start: int) -> dict:
        return {
            'SortByV2': {'Key': 'PostedDate', 'Order': 2},
            'BunitIds': UNFILTERED,
            'Experience': UNFILTERED,
            'JobTypes': UNFILTERED,
            'JobTypeV2': UNFILTERED,
            'Locations': UNFILTERED,
            'CreatedDate': UNFILTERED,
            'Compensation': UNFILTERED,
            'Skills': UNFILTERED,
            'Keyword': self.keyword,
            'ClientIds': UNFILTERED,
            'Department': '',
            'CustomFields': {},
        }

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('Result') or []

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        if start > 0:
            return ListingPage(stop=True)

        response = post_with_retry(
            lambda: self._session,
            self.list_url,
            params={'orgId': self.org_id, 'pageType': 0},
            json=self.build_list_params(start),
            headers={**self._referer_headers, 'Authorization': f'Bearer {self._get_access_token()}'},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        listings = []
        for item in self.parse_list_items(self._parse_json(response)):
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)
        return ListingPage(listings=listings, stop=True)

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        obfuscated_id = item.get('JobIdObfuscated')
        if not obfuscated_id:
            self._record_error(None, f'missing job id: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(f'https://{self.host}/job/publicjobs/{obfuscated_id}'),
            official_id=clean_text(item.get('JobCode')) or None,
            title=clean_text(item.get('JobTitle')),
            company_name=self.company_name,
            location=clean_text(_build_location_text(item.get('Location'))),
            extra={'description': item.get('JobDescV2')},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        return {'description': clean_text(listing.extra.get('description'))}

    def parse_detail_fields(self, response_json: dict) -> dict:
        return {'description': clean_text(response_json.get('JobDescV2'))}


def _build_location_text(raw_location: str | None) -> str | None:
    """`Location` is a JSON-encoded string holding a list of `{Address, ...}` dicts."""
    if not raw_location:
        return None
    try:
        locations = json.loads(raw_location)
    except (TypeError, ValueError):
        return raw_location
    addresses = [location.get('Address') for location in locations if isinstance(location, dict)]
    return '; '.join(address for address in addresses if address) or None
