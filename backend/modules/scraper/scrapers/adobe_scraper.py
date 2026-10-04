from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'adobe.wd5.myworkdayjobs.com'
TENANT = 'adobe'
SITE = 'external_experienced'
COMPANY_NAME = 'Adobe'

APPLIED_FACETS = {
    'jobFamilyGroup': ['591af8b812fa10737af39db3d96eed9f'],  # Engineering
    'workerSubType': ['3ba4ecdf4893100b2f8d06b0870c6c8b'],  # Regular
    'timeType': ['262714769a02100a80d2a64ac4e040c0'],  # Full time
    'locationCountry': ['c4f78be1a8f14da0ab49ce1162348a5e'],  # India
}


@register_scraper
class AdobeScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.ADOBE

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
