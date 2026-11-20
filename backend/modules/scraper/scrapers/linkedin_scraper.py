import secrets
import threading

from bs4 import BeautifulSoup
from curl_cffi import requests

from common.utils.env import get_env
from common.utils.http import get_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url, extract_linkedin_job_id
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS, SECONDS_PER_HOUR
from modules.scraper.utils.http_session import new_session
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.text_cleaner import clean_text

LISTING_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
DETAIL_URL_TEMPLATE = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
SEARCH_PAGE_REFERER = 'https://www.linkedin.com/jobs/search'
PAGE_SIZE = 10
MAX_CONSECUTIVE_EMPTY_PAGES = 5
PROXY_HOST_ENV_KEY = 'SCRAPER_PROXY_HOST'
PROXY_PORT_ENV_KEY = 'SCRAPER_PROXY_PORT'
PROXY_USERNAME_ENV_KEY = 'SCRAPER_PROXY_USERNAME'
PROXY_PASSWORD_ENV_KEY = 'SCRAPER_PROXY_PASSWORD'

DEFAULT_SEARCH_FILTERS = {
    'keywords': 'software',
    'location': 'India',
    'f_E': '2,3,4',
}


def _new_session(scraper: 'LinkedInScraper') -> requests.Session:
    """Build a fresh session with a new proxy exit IP (a fresh random impersonate
    profile/fingerprint is handled by new_session itself)."""
    proxy_url = scraper._build_proxy_url(secrets.token_hex(8))
    return new_session(proxy_url)


class _ProxyLane:
    """A session used by one worker thread at a time. On retry the current session is discarded
    and a brand new one is used instead, since a failure is usually tied to the specific IP/fingerprint
    combo."""

    def __init__(self, scraper: 'LinkedInScraper', label: str):
        self._scraper = scraper
        self._label = label
        self.session = _new_session(scraper)

    def request(self, url: str, **kwargs) -> requests.Response:
        def on_retry():
            self.session = _new_session(self._scraper)

        return get_with_retry(lambda: self.session, url, on_retry=on_retry, **kwargs)


@register_scraper
class LinkedInScraper(BaseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.LINKEDIN

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    def __init__(self):
        super().__init__()

        self._proxy_host = get_env(PROXY_HOST_ENV_KEY)
        self._proxy_port = get_env(PROXY_PORT_ENV_KEY)
        self._proxy_username = get_env(PROXY_USERNAME_ENV_KEY)
        self._proxy_password = get_env(PROXY_PASSWORD_ENV_KEY)

        self._listing_lane = _ProxyLane(self, label='listing')

        self._thread_local = threading.local()
        self._lane_counter = 0
        self._lane_counter_lock = threading.Lock()

        self._consecutive_empty_pages = 0

    def _reset_run_state(self) -> None:
        super()._reset_run_state()
        self._consecutive_empty_pages = 0

    def _build_proxy_url(self, session_id: str) -> str:
        username = f'{self._proxy_username}__sessid.{session_id}'
        return f'http://{username}:{self._proxy_password}@{self._proxy_host}:{self._proxy_port}'

    def _get_detail_lane(self) -> _ProxyLane:
        lane = getattr(self._thread_local, 'lane', None)
        if lane is None:
            with self._lane_counter_lock:
                self._lane_counter += 1
                label = f'detail-{self._lane_counter}'
            lane = _ProxyLane(self, label=label)
            self._thread_local.lane = lane
        return lane

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        html = self._fetch_listing_html(start, time_range_hours)
        page_listings = self._parse_listing_html(html)

        if not page_listings:
            self._consecutive_empty_pages += 1
            if self._consecutive_empty_pages >= MAX_CONSECUTIVE_EMPTY_PAGES:
                self._logger.info(
                    'stopping pagination after %s consecutive empty pages', self._consecutive_empty_pages
                )
                return ListingPage(stop=True)
            return ListingPage()

        self._consecutive_empty_pages = 0
        return ListingPage(listings=page_listings)

    def _fetch_listing_html(self, start: int, time_range_hours: int) -> str:
        time_range_seconds = time_range_hours * SECONDS_PER_HOUR
        params = {**DEFAULT_SEARCH_FILTERS, 'f_TPR': f'r{time_range_seconds}', 'start': start}
        wait_between_requests()
        response = self._listing_lane.request(
            LISTING_URL,
            params=params,
            headers={'Referer': SEARCH_PAGE_REFERER},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text

    def _parse_listing_html(self, html: str) -> list[ScraperJobData]:
        soup = BeautifulSoup(html, 'html.parser')
        listings = []

        for card in soup.find_all('li'):
            link = card.find('a', class_='base-card__full-link')
            if link is None or not link.get('href'):
                continue

            raw_url = link['href'].strip()
            job_id = extract_linkedin_job_id(raw_url)
            if job_id is None:
                self._record_error(raw_url, 'could not extract job id from url')
                continue

            title_el = card.find('h3', class_='base-search-card__title')
            company_el = card.find('h4', class_='base-search-card__subtitle')
            location_el = card.find('span', class_='job-search-card__location')

            listings.append(
                ScraperJobData(
                    url=clean_job_url(raw_url),
                    title=clean_text(title_el.get_text(strip=True) if title_el else None),
                    company_name=clean_text(company_el.get_text(strip=True) if company_el else None),
                    location=clean_text(location_el.get_text(strip=True) if location_el else None),
                    extra={'job_id': job_id},
                )
            )

        return listings

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        return {'description': self._fetch_job_details(listing.extra['job_id'], referer=listing.url)}

    def _fetch_job_details(self, job_id: str, referer: str) -> str | None:
        wait_between_requests()

        detail_url = DETAIL_URL_TEMPLATE.format(job_id=job_id)
        response = self._get_detail_lane().request(
            detail_url,
            headers={'Referer': referer},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self._parse_detail_html(response.text)

    def _parse_detail_html(self, html: str) -> str | None:
        soup = BeautifulSoup(html, 'html.parser')
        description_el = soup.find('div', class_='show-more-less-html__markup')
        if description_el is None:
            return None
        return clean_text(description_el.get_text(separator='\n', strip=True))
