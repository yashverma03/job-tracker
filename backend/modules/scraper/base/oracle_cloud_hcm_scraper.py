from abc import abstractmethod

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

FACETS_LIST = 'LOCATIONS;WORK_LOCATIONS;WORKPLACE_TYPES;TITLES;CATEGORIES;ORGANIZATIONS;POSTING_DATES;FLEX_FIELDS'
LAST_SELECTED_FACET = 'POSTING_DATES'
SORT_BY = 'POSTING_DATES_DESC'
LIST_EXPAND = (
    'requisitionList.workLocation,requisitionList.otherWorkLocations,'
    'requisitionList.secondaryLocations,flexFieldsFacet.values,requisitionList.requisitionFlexFields'
)

# Job-specific detail fields to concatenate into the stored description - excludes the
# generic company/EEO boilerplate fields (e.g. CorporateDescriptionStr) that repeat
# identically across every posting.
DESCRIPTION_FIELDS = ('ExternalDescriptionStr', 'ExternalResponsibilitiesStr', 'ExternalQualificationsStr')
# Location fields to concatenate, in priority order. The list-item fields (secondary/
# other/work locations) are lists of dicts with a `Name` key; the primary location is a
# plain string.
LOCATION_LIST_FIELDS = ('secondaryLocations', 'otherWorkLocations', 'workLocation')


class OracleCloudHcmScraper(ApiScraper):
    """Base for scrapers targeting a company's Oracle Cloud HCM (Fusion Recruiting
    Cloud) careers site (`*.oraclecloud.com`). Many companies (Oracle included) run
    their external career site on this platform, sharing the same list/detail API
    shape and `finder=` query-string search syntax - only the host, site number and
    search-scoping facets differ. Subclasses only need to implement the properties
    below; pagination and request/response handling are handled here."""

    @property
    @abstractmethod
    def host(self) -> str:
        """e.g. 'eeho.fa.us2.oraclecloud.com'."""

    @property
    @abstractmethod
    def site_number(self) -> str:
        """The tenant's careers site number used in the `finder` query, e.g. 'CX_45001'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Oracle'."""

    @property
    @abstractmethod
    def job_url_template(self) -> str:
        """Public job URL format with a `{job_id}` placeholder, e.g.
        'https://careers.oracle.com/en/sites/jobsearch/job/{job_id}'."""

    @property
    def selected_flex_fields_facets(self) -> str | None:
        """Raw value for the finder's `selectedFlexFieldsFacets` filter (tenant-defined
        custom fields, e.g. employment type / seniority) - override to scope the search
        per company. `None` omits the filter."""
        return None

    @property
    def selected_locations_facet(self) -> str | None:
        """Facet id for the finder's `selectedLocationsFacet` filter. `None` omits it."""
        return None

    @property
    def selected_categories_facet(self) -> str | None:
        """Facet id for the finder's `selectedCategoriesFacet` filter (job family/
        category, e.g. Software Engineering). `None` omits it."""
        return None

    @property
    def selected_titles_facet(self) -> str | None:
        """Value for the finder's `selectedTitlesFacet` filter (job-title grouping,
        e.g. 'ENG' for Engineering). `None` omits it."""
        return None

    @property
    def selected_posting_dates_facet(self) -> str | None:
        """Value for the finder's `selectedPostingDatesFacet` filter. `None` omits it."""
        return None

    @property
    def list_url(self) -> str:
        return f'https://{self.host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions'

    @property
    def detail_url_template(self) -> str:
        return f'https://{self.host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails/{{job_id}}'

    @property
    def detail_url(self) -> str:
        # Unused: `_fetch_detail_fields` is overridden below since the detail URL is
        # templated on each listing's own job id, not a fixed endpoint.
        return self.detail_url_template

    def _build_finder(self, start: int) -> str:
        parts = [
            f'findReqs;siteNumber={self.site_number}',
            f'facetsList={FACETS_LIST}',
            f'limit={self.page_size},offset={start}',
            f'lastSelectedFacet={LAST_SELECTED_FACET}',
        ]
        if self.selected_flex_fields_facets is not None:
            parts.append(f'selectedFlexFieldsFacets="{self.selected_flex_fields_facets}"')
        if self.selected_locations_facet is not None:
            parts.append(f'selectedLocationsFacet={self.selected_locations_facet}')
        if self.selected_categories_facet is not None:
            parts.append(f'selectedCategoriesFacet={self.selected_categories_facet}')
        if self.selected_titles_facet is not None:
            parts.append(f'selectedTitlesFacet={self.selected_titles_facet}')
        if self.selected_posting_dates_facet is not None:
            parts.append(f'selectedPostingDatesFacet={self.selected_posting_dates_facet}')
        parts.append(f'sortBy={SORT_BY}')
        return ','.join(parts)

    def build_list_params(self, start: int) -> dict:
        return {
            'onlyData': 'true',
            'expand': LIST_EXPAND,
            'finder': self._build_finder(start),
        }

    def parse_list_items(self, response_json: dict) -> list[dict]:
        items = response_json.get('items') or []
        return items[0].get('requisitionList', []) if items else []

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('Id')
        if not job_id:
            self._record_error(None, f'missing job id: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(self.job_url_template.format(job_id=job_id)),
            official_id=str(job_id),
            title=clean_text(item.get('Title')),
            company_name=self.company_name,
            location=clean_text(_build_location_text(item)),
            extra={'job_id': job_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(
            self.detail_url_template.format(job_id=listing.extra['job_id']),
            params={'onlyData': 'true', 'expand': 'all'},
        )
        response.raise_for_status()
        return self.parse_detail_fields(self._parse_json(response))

    def parse_detail_fields(self, response_json: dict) -> dict:
        description = '\n\n'.join(text for text in (response_json.get(field) for field in DESCRIPTION_FIELDS) if text)

        return {
            'description': clean_text(description),
            'location': clean_text(_build_location_text(response_json)),
        }


def _build_location_text(fields: dict) -> str | None:
    names = []
    primary_location = fields.get('PrimaryLocation')
    if primary_location:
        names.append(primary_location)

    for field_name in LOCATION_LIST_FIELDS:
        for location in fields.get(field_name) or []:
            name = location.get('Name')
            if name and name not in names:
                names.append(name)

    return ', '.join(names) if names else None
