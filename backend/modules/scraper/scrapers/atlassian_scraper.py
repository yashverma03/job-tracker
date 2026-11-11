from modules.scraper.base.icims_scraper import IcimsScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

LISTINGS_URL = 'https://www.atlassian.com/endpoint/careers/listings'
JOB_URL_TEMPLATE = 'https://www.atlassian.com/company/careers/details/{job_id}'
COMPANY_NAME = 'Atlassian'
ALLOWED_CATEGORIES = {'engineering', 'security'}
LOCATION_KEYWORDS = ('india', 'remote')


@register_scraper
class AtlassianScraper(IcimsScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.ATLASSIAN

    @property
    def list_url(self) -> str:
        return LISTINGS_URL

    @property
    def job_url_template(self) -> str:
        return JOB_URL_TEMPLATE

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def allowed_categories(self) -> set[str]:
        return ALLOWED_CATEGORIES

    @property
    def location_keywords(self) -> tuple[str, ...]:
        return LOCATION_KEYWORDS
