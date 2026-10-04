from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'mastercard.wd1.myworkdayjobs.com'
TENANT = 'mastercard'
SITE = 'CorporateCareers'
COMPANY_NAME = 'Mastercard'

APPLIED_FACETS = {
    'jobFamilyGroup': ['189119ebe266100103737c3d6a6e0000'],  # Engineering
    'workerSubType': ['4989ab17f4c24a42a64a54369451fb0b'],  # Regular
}


@register_scraper
class MastercardScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.MASTERCARD

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
