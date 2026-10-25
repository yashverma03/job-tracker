from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'visa.wd5.myworkdayjobs.com'
TENANT = 'visa'
SITE = 'Visa'
COMPANY_NAME = 'Visa'

APPLIED_FACETS = {
    'locationCountry': ['c4f78be1a8f14da0ab49ce1162348a5e'],
    'jobFamilyGroup': [
        'e8c806498390105c6260a580252a0363',
        'd48eccdc23121000b8a44df0bd370000',
    ],
}


@register_scraper
class VisaScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.VISA

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
