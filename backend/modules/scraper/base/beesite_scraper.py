import json
from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

DEFAULT_MATCHED_OBJECT_FIELDS = (
    'PositionID',
    'PositionTitle',
    'PositionURI',
    'PositionLocation.CityName',
    'PositionLocation.CountryName',
    'PublicationStartDate',
    'OrganizationName',
)
DEFAULT_PAGE_SIZE = 100000


def _build_location_text(locations: list[dict] | None) -> str | None:
    if not locations:
        return None
    names = []
    for location in locations:
        parts = [part for part in (location.get('CityName'), location.get('CountryName')) if part]
        name = ', '.join(parts)
        if name and name not in names:
            names.append(name)
    return '; '.join(names) if names else None


class BeesiteScraper(ApiScraper):
    """Base for scrapers targeting a Beesite-hosted careers search API
    (`api-<company>.beesite.de`). Beesite (by Milch & Zucker) is a shared multi-tenant
    ATS/search-widget vendor used by several large (mostly DAX-listed) companies to
    power their careers-site job search - the `search/` (list, a GET whose `data` query
    param is a URL-encoded JSON search request) and `jobhtml/<id>.json` (detail) endpoint
    pair, their request/response shape, and the `SearchCriteria` facet-filter format are
    identical across tenants; only the host, company display name, canonical job URL
    format and this company's own facet-filter values (location/profession/category
    facet ids - tenant-specific, found by inspecting that tenant's own career site facet
    counts) differ. Subclasses only need to implement the properties below.

    Verified live against Deutsche Bank's tenant (`api-deutschebank.beesite.de`):
    `SearchParameters.FirstItem` is a 1-indexed offset that actually advances the
    result set, `SearchCriteria` entries use `CriterionName`/`CriterionValue` (the
    location facet keys off the bare facet name, e.g. `PositionLocation.Country`, while
    the profession/category facets key off a `.Code` suffix, e.g.
    `ProfessionCategory.Code` - confirmed by diffing `SearchResultCountAll` against each
    facet's own reported `Count` for that term), and the server did not clamp
    `CountItem` at any value tried up to 100000 (it just returns however many results
    actually match)."""

    @property
    @abstractmethod
    def host(self) -> str:
        """e.g. 'api-deutschebank.beesite.de'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Deutsche Bank'."""

    @property
    @abstractmethod
    def job_url_template(self) -> str:
        """Public job URL format with a `{position_id}` placeholder, e.g.
        'https://careers.db.com/professionals/search-roles/#/professional/job/{position_id}'."""

    @property
    def search_criteria(self) -> list[dict]:
        """This tenant's `SearchCriteria` filters (location/profession/category facet
        ids, etc.), each as `{'CriterionName': ..., 'CriterionValue': [...]}` - override
        to scope the search per company. Empty by default (unscoped search)."""
        return []

    @property
    def matched_object_descriptor_fields(self) -> tuple[str, ...]:
        """Fields requested from the search endpoint's MatchedObjectDescriptor. Override
        to request extra fields a subclass's `map_item_to_listing` needs."""
        return DEFAULT_MATCHED_OBJECT_FIELDS

    @property
    def language_code(self) -> str:
        # Verified live: a lowercase/mixed-case value (e.g. 'en', 'en-US') is silently
        # ignored and the API falls back to German ('DE') location/field names; only an
        # exact uppercase 'EN' actually switches the response to English.
        return 'EN'

    @property
    def page_size(self) -> int:
        return DEFAULT_PAGE_SIZE

    @property
    def list_url(self) -> str:
        return f'https://{self.host}/search/'

    @property
    def detail_url_template(self) -> str:
        return f'https://{self.host}/jobhtml/{{position_id}}.json'

    @property
    def detail_url(self) -> str:
        # Unused: `_fetch_detail_fields` is overridden below since the per-job detail
        # URL is templated on each listing's own position id, not a fixed endpoint.
        return self.detail_url_template

    def build_list_params(self, start: int) -> dict:
        payload = {
            'LanguageCode': self.language_code,
            'SearchParameters': {
                'FirstItem': start + 1,
                'CountItem': self.page_size,
                'MatchedObjectDescriptor': list(self.matched_object_descriptor_fields),
                'Sort': [{'Criterion': 'PublicationStartDate', 'Direction': 'DESC'}],
            },
            'SearchCriteria': list(self.search_criteria),
        }
        return {'data': json.dumps(payload)}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return (response_json.get('SearchResult') or {}).get('SearchResultItems') or []

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        descriptor = item.get('MatchedObjectDescriptor') or {}
        position_id = descriptor.get('PositionID') or item.get('MatchedObjectId')
        if not position_id:
            self._record_error(None, f'missing PositionID: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(self.job_url_template.format(position_id=position_id)),
            official_id=self._resolve_official_id(descriptor, position_id),
            title=clean_text(descriptor.get('PositionTitle')),
            company_name=self.company_name,
            location=clean_text(_build_location_text(descriptor.get('PositionLocation'))),
            extra={'position_id': position_id},
        )

    def _resolve_official_id(self, descriptor: dict, position_id: str) -> str | None:
        """`PositionID` is Beesite's own transient listing slot, not the tenant's real,
        publicly displayed requisition id - override to derive the latter from
        `descriptor` (requesting whatever extra `matched_object_descriptor_fields` it
        takes). Returns `None` by default: `PositionID` must never be used as a
        stand-in `official_id`, since `job_unique_key_service` dedup keys on it, and a
        wrong id is worse than a missing one."""
        return None

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(self.detail_url_template.format(position_id=listing.extra['position_id']))
        response.raise_for_status()
        return self.parse_detail_fields(self._parse_json(response))

    def parse_detail_fields(self, response_json: dict) -> dict:
        return {'description': clean_text(response_json.get('html'))}
