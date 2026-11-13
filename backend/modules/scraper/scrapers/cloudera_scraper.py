from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'cloudera.wd5.myworkdayjobs.com'
TENANT = 'cloudera'
SITE = 'External_Career'
COMPANY_NAME = 'Cloudera'

APPLIED_FACETS = {
    'locationCountry': ['c4f78be1a8f14da0ab49ce1162348a5e'],  # India
}


@register_scraper
class ClouderaScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.CLOUDERA

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
