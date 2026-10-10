import json
from abc import abstractmethod

from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text


class RadancyScraper(ApiScraper):
    """Base for scrapers targeting a Radancy/TalentBrew-hosted careers site (identifiable
    by `talentbrew.com`/`radancy.net` references in the page's CSP headers and assets). The list endpoint (`<host>/search-jobs/results`) takes
    ASP.NET-model-bound query params (`CurrentPage`, `RecordsPerPage`,
    `FacetFilters[i].ID/FacetType/Display/IsApplied/FieldName`, plus a handful of other
    decorative params the endpoint 400s without) and returns a JSON envelope whose
    `results` field is an HTML fragment of job list items; the job detail page (the
    listing's own URL, not a separate JSON endpoint) embeds a `JobPosting` JSON-LD block
    with the full description. All of that plumbing lives here - subclasses only supply
    the host, company name, and this company's fixed facet-filter query params."""

    @property
    @abstractmethod
    def host(self) -> str:
        """e.g. 'jobs.citi.com'."""

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Display name to store on the job, e.g. 'Citi'."""

    @property
    @abstractmethod
    def search_params(self) -> dict:
        """This company's fixed search query params (ActiveFacetID, `FacetFilters[i].*`
        for each applied facet, SortCriteria, SearchType, etc.), exactly as the site's
        own search UI sends them - everything except CurrentPage/RecordsPerPage/
        IsPagination/TotalContentResults/TotalContentPages, which are filled in per-page
        below."""

    @property
    def page_size(self) -> int:
        # Sent as RecordsPerPage; large enough that the single request in
        # `_fetch_listing_page` returns every matching job in one response.
        return 10000

    @property
    def list_url(self) -> str:
        return f'https://{self.host}/search-jobs/results'

    @property
    def detail_url(self) -> str:
        # Unused: detail is fetched from each listing's own URL, see `_fetch_detail_fields`.
        return f'https://{self.host}'

    def build_list_params(self, start: int) -> dict:
        current_page = start // self.page_size + 1
        params = dict(self.search_params)
        params.update(
            {
                'CurrentPage': current_page,
                'RecordsPerPage': self.page_size,
                'TotalContentResults': '',
                'IsPagination': 'False',
                'TotalContentPages': 'NaN',
            }
        )
        return params

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        # A large enough RecordsPerPage returns every matching job in a single
        # response on this platform - there's no real "next page" to request, so
        # always stop after the first (and only) call.
        response = self._request(self.list_url, params=self.build_list_params(start))
        response.raise_for_status()
        items = self.parse_list_items(self._parse_json(response))

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings, stop=True)

    def parse_list_items(self, response_json: dict) -> list[dict]:
        soup = BeautifulSoup(response_json.get('results') or '', 'html.parser')
        items = []
        for link in soup.select('a[data-job-id]'):
            container = link.find_parent('li') or link.parent
            location_el = container.select_one('[class*="job-location"]') if container else None
            # Title markup varies per tenant: some put the title text directly inside
            # the link; others wrap the link in a title element instead and nest the
            # location element inside the link alongside a title element of its own.
            # Prefer the link's own direct text; if it has none (title lives in a
            # child element instead), fall back to the link's children, excluding
            # whichever one is the location element, so location text never leaks in.
            direct_text = link.find(string=True, recursive=False)
            if direct_text and direct_text.strip():
                title = direct_text.strip()
            else:
                child_texts = [
                    child.get_text(strip=True) for child in link.find_all(recursive=False) if child is not location_el
                ]
                title = ' '.join(text for text in child_texts if text)
            items.append(
                {
                    'job_id': link.get('data-job-id'),
                    'href': link.get('href'),
                    'title': title,
                    'location': location_el.get_text(strip=True) if location_el else None,
                }
            )
        return items

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('job_id')
        href = item.get('href')
        if not job_id or not href:
            self._record_error(None, f'missing job id or href: {item}')
            return None

        # job_id is Radancy's internal posting ID, not the real Job ID - only used for
        # the URL. official_id comes from the detail page (see parse_detail_fields).
        return ScraperJobData(
            url=clean_job_url(f'https://{self.host}{href}'),
            title=clean_text(item.get('title')),
            company_name=self.company_name,
            location=clean_text(item.get('location')),
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.url)
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
            except (TypeError, ValueError):
                continue
            if data.get('@type') == 'JobPosting':
                fields = {'description': clean_text(data.get('description'))}
                # The page's own Job ID - the employer-facing identifier, as opposed to
                # the URL's numeric ID, which is Radancy's internal posting ID. Rendered
                # as a bare string on some tenants, a PropertyValue object on others.
                identifier = data.get('identifier')
                identifier = identifier.get('value') if isinstance(identifier, dict) else identifier
                if identifier:
                    fields['official_id'] = str(identifier).strip()
                return fields

        return {'description': None}
