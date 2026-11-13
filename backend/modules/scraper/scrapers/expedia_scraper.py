from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'expedia.wd108.myworkdayjobs.com'
TENANT = 'expedia'
SITE = 'search'
COMPANY_NAME = 'Expedia'

APPLIED_FACETS = {
    'jobFamilyGroup': ['c553432013ba103b60decedc3beb2900'],  # Technology Group
    'locations': [
        'c553432013ba103bbc5cc6e3faef5396',  # India - Gurgaon
        'c553432013ba103bbc5b28efceb250b1',  # India - Bangalore
        'c3ebb72cd55510002eb24e76221c0000',  # IND0011 - Gurgaon - Downtown - Expedia
    ],
}


@register_scraper
class ExpediaScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.EXPEDIA

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
