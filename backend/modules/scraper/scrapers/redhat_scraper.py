from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'redhat.wd5.myworkdayjobs.com'
TENANT = 'redhat'
SITE = 'jobs'
COMPANY_NAME = 'RedHat'

APPLIED_FACETS = {
    'a': ['c4f78be1a8f14da0ab49ce1162348a5e'],  # Country: India
    'd': ['c18026e77576010f6ef6126f4e43ec4a'],  # Job Function: Engineering
}


@register_scraper
class RedhatScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.REDHAT

    @property
    def workday_host(self) -> str:
        return WORKDAY_HOST

    @property
    def tenant(self) -> str:
        return TENANT

    @property
    def site(self) -> str:
        return SITE

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def applied_facets(self) -> dict:
        return APPLIED_FACETS
