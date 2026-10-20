import copy
import json
import re
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from common.utils.env import get_env
from common.utils.http import get_with_retry, post_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.http_session import new_session
from modules.scraper.utils.text_cleaner import clean_text

LOGIN_URL = 'https://wellfound.com/login'
JOBS_URL = 'https://wellfound.com/jobs'
GRAPHQL_URL = 'https://wellfound.com/graphql'
JOB_URL_TEMPLATE = 'https://wellfound.com/jobs/{job_id}-{slug}'
NEXT_DATA_PATTERN = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

EMAIL_ENV_KEY = 'SCRAPER_WELLFOUND_EMAIL'
PASSWORD_ENV_KEY = 'SCRAPER_WELLFOUND_PASSWORD'

SESSION_COOKIE_NAME = '_wellfound'
JOB_SEARCH_OPERATION = 'JobSearchResultsX'
SORT_BY_MOST_RECENT = 'LAST_POSTED'
MAX_LISTING_PAGES = 100
REQUEST_DELAY_SECONDS = 3

NAVIGATION_TIMEOUT_MS = 45000

NETWORK_RETRY_INITIAL_DELAY_SECONDS = 5
NETWORK_RETRY_MAX_TOTAL_WAIT_SECONDS = 120


def _is_job_search_request(request) -> bool:
    if request.method != 'POST' or not request.url.startswith(GRAPHQL_URL):
        return False
    try:
        body = request.post_data_json
    except Exception:  # noqa: BLE001
        return False
    return isinstance(body, dict) and body.get('operationName') == JOB_SEARCH_OPERATION


@register_scraper
class WellfoundScraper(BaseScraper):
    """Logs in once with Playwright to get the session cookie and the signed headers
    Wellfound's GraphQL gateway expects (the signature is minted by the page's own
    JavaScript, so it can't be built without a browser), then pages through the job
    search API and fetches job pages over plain HTTP.

    The browser is only opened for that bootstrap, lazily on the first request, and is
    closed before any listing or detail request goes out. The captured search request
    is reused as the template, so the account's saved search filters apply. Every request
    is spaced out by `REQUEST_DELAY_SECONDS` to stay clear of rate limiting."""

    @property
    def name(self) -> ScraperName:
        return ScraperName.WELLFOUND

    @property
    def page_size(self) -> int:
        return 1

    @property
    def detail_worker_count(self) -> int:
        return 1

    def __init__(self):
        super().__init__()
        self._session = new_session()
        self._request_template: dict | None = None
        self._api_headers: dict = {}
        self._seen_job_ids: set = set()

    def _reset_run_state(self) -> None:
        super()._reset_run_state()
        self._seen_job_ids = set()

    def close(self) -> None:
        self._session.close()

    def _with_network_retry(self, fn, *args, **kwargs):
        """Retries a Playwright-driven action on transient network/navigation errors
        (connection resets, DNS blips, navigation timeouts) with exponential backoff,
        so a momentary internet drop doesn't kill an entire run. Keeps retrying until
        the cumulative wait would exceed NETWORK_RETRY_MAX_TOTAL_WAIT_SECONDS, at which
        point the next failure is raised. Non-network exceptions (e.g. a missing
        element, bad login credentials) propagate immediately."""
        delay = NETWORK_RETRY_INITIAL_DELAY_SECONDS
        elapsed = 0
        while True:
            try:
                return fn(*args, **kwargs)
            except PlaywrightError as exc:
                if elapsed >= NETWORK_RETRY_MAX_TOTAL_WAIT_SECONDS:
                    raise
                sleep_for = min(delay, NETWORK_RETRY_MAX_TOTAL_WAIT_SECONDS - elapsed)
                self._logger.warning(
                    'transient network error, retrying in %ss (%ss/%ss elapsed): %s',
                    sleep_for,
                    elapsed,
                    NETWORK_RETRY_MAX_TOTAL_WAIT_SECONDS,
                    exc,
                )
                time.sleep(sleep_for)
                elapsed += sleep_for
                delay *= 2

    def _bootstrap_session(self) -> None:
        email = get_env(EMAIL_ENV_KEY)
        password = get_env(PASSWORD_ENV_KEY)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                page = context.new_page()

                page.goto(LOGIN_URL, wait_until='load', timeout=NAVIGATION_TIMEOUT_MS)
                page.fill('input[name=username]', email)
                page.fill('input[name=password]', password)
                with page.expect_navigation(timeout=30000):
                    page.click('input[type=submit]')

                session_cookie = next(
                    (cookie.get('value') for cookie in context.cookies() if cookie.get('name') == SESSION_COOKIE_NAME),
                    None,
                )
                if session_cookie is None:
                    raise RuntimeError('Wellfound login failed: no session cookie set after login attempt')

                with page.expect_request(_is_job_search_request, timeout=NAVIGATION_TIMEOUT_MS) as request_info:
                    page.goto(JOBS_URL, wait_until='load', timeout=NAVIGATION_TIMEOUT_MS)
                search_request = request_info.value
                signature = search_request.all_headers().get('x-apollo-signature')
                if not signature:
                    raise RuntimeError('Wellfound job search request had no x-apollo-signature header')
                request_template = search_request.post_data_json
            finally:
                browser.close()

        self._session.cookies.clear()
        self._session.cookies.set(SESSION_COOKIE_NAME, session_cookie, domain='wellfound.com')
        self._api_headers = {
            'x-apollo-signature': signature,
            'x-apollo-operation-name': JOB_SEARCH_OPERATION,
            'x-requested-with': 'XMLHttpRequest',
            'referer': JOBS_URL,
        }
        self._request_template = request_template
        self._logger.info('logged into Wellfound as %s', email)

    def _throttled(self, send):
        time.sleep(REQUEST_DELAY_SECONDS)
        return send()

    def _search_jobs(self, page_number: int) -> dict:
        if self._request_template is None:
            self._with_network_retry(self._bootstrap_session)
        body = copy.deepcopy(self._request_template or {})
        filters = body['variables']['filterConfigurationInput']
        filters['page'] = page_number
        filters['sortBy'] = SORT_BY_MOST_RECENT

        response = self._throttled(
            lambda: post_with_retry(
                lambda: self._session,
                GRAPHQL_URL,
                json=body,
                headers=self._api_headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        )
        response.raise_for_status()
        response_json = response.json()
        if response_json.get('data', {}).get('talent', {}).get('jobSearchResults') is None:
            raise RuntimeError(f'unexpected job search response: {json.dumps(response_json)[:2000]}')
        return response_json

    def _startup_nodes(self, edges: list[dict]) -> list[dict]:
        startups = []
        for edge in edges:
            node = edge.get('node') or {}
            if node.get('__typename') == 'FeaturedStartups':
                startups.extend(node.get('featuredStartups') or [])
            else:
                startups.append(node)
        return startups

    def _search_edges(self, response_json: dict) -> list[dict]:
        return response_json['data']['talent']['jobSearchResults'].get('startups', {}).get('edges', [])

    def _parse_list_items(self, edges: list[dict]) -> list[dict]:
        items = []
        for node in self._startup_nodes(edges):
            startup = node.get('promotedStartup') or node
            startup_name = startup.get('name')
            for job_listing in startup.get('highlightedJobListings') or []:
                items.append({**job_listing, '_startup_name': startup_name})
        return items

    def _map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id')
        slug = item.get('slug')
        if not job_id or not slug:
            self._record_error(None, f'missing id or slug: {item}')
            return None

        location_names = item.get('locationNames') or []
        if location_names:
            location = '; '.join(location_names)
        elif item.get('remote'):
            location = 'Remote'
        else:
            location = 'Unknown'

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(job_id=job_id, slug=slug)),
            title=clean_text(item.get('title')),
            company_name=clean_text(item.get('_startup_name')),
            location=clean_text(location),
            extra={'job_id': job_id, 'slug': slug},
        )

    def _fetch_listing_page(self, start: int, _time_range_hours: int) -> ListingPage:
        page_number = start // self.page_size + 1
        edges = self._search_edges(self._search_jobs(page_number))

        listings = []
        has_new_jobs = False
        for item in self._parse_list_items(edges):
            job_id = item.get('id')
            if job_id is None or job_id in self._seen_job_ids:
                continue
            has_new_jobs = True
            self._seen_job_ids.add(job_id)

            listing = self._map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        self._logger.info('page %s: %s new jobs', page_number, len(listings))
        # Past the last real page Wellfound keeps re-serving the same few promoted startups.
        return ListingPage(listings=listings, stop=not has_new_jobs or page_number >= MAX_LISTING_PAGES)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._throttled(
            lambda: get_with_retry(lambda: self._session, listing.url, timeout=REQUEST_TIMEOUT_SECONDS)
        )
        response.raise_for_status()

        match = NEXT_DATA_PATTERN.search(response.text)
        if match is None:
            raise RuntimeError(f'could not find __NEXT_DATA__ on {listing.url}')

        next_data = json.loads(match.group(1))
        apollo_data = next_data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
        job_listing = apollo_data.get(f'JobListing:{listing.extra["job_id"]}') or {}

        description = clean_text(job_listing.get('descriptionHtml') or job_listing.get('description'))
        compensation = job_listing.get('compensation')
        if compensation:
            description = f'Salary: {compensation}\n\n{description}' if description else f'Salary: {compensation}'

        return {'description': description}
