from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'walmart.wd504.myworkdayjobs.com'
TENANT = 'walmart'
SITE = 'WalmartExternal'
COMPANY_NAME = 'Walmart'

APPLIED_FACETS = {
    'locationCountry': ['c4f78be1a8f14da0ab49ce1162348a5e'],  # India
    'jobFamilyGroup': [
        'e83ebdbd2a0a01e7e1477a8948e904c6',  # Technology
        'e83ebdbd2a0a01af0185848948e94dc6',  # Data Analytics and Management
    ],
}


@register_scraper
class WalmartScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.WALMART

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
