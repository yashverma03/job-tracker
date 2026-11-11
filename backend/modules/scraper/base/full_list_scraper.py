from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.types import ListingPage, ScraperJobData

PAGE_SIZE = 10000


class FullListScraper(ApiScraper):
    """Base for sources whose list endpoint can't be paged or filtered server-side and
    always returns every job in one response (Greenhouse, Atlassian's iCIMS feed). That
    one response is fetched at most once per run, scoped locally via `include_job`, and
    sliced to satisfy `ApiScraper`'s offset-based paging contract - no extra HTTP calls
    past the first."""

    def __init__(self):
        super().__init__()
        self._all_jobs: list[dict] | None = None

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_query_params(self) -> dict:
        return {}

    def build_list_params(self, _start: int) -> dict:
        return self.list_query_params

    def build_detail_params(self, _listing: ScraperJobData) -> dict:
        return {}

    def include_job(self, _item: dict) -> bool:
        """Local scoping of the full list (country, department, ...). Default: keep all."""
        return True

    def _fetch_all_jobs(self) -> list[dict]:
        if self._all_jobs is None:
            response = self._request(self.list_url, params=self.list_query_params)
            response.raise_for_status()
            items = self.parse_list_items(self._parse_json(response))
            self._all_jobs = [item for item in items if self.include_job(item)]
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
