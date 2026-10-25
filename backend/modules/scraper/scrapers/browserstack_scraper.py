from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'browserstack.wd3.myworkdayjobs.com'
TENANT = 'browserstack'
SITE = 'External'
COMPANY_NAME = 'BrowserStack'

APPLIED_FACETS = {
    'locations': [
        '880034dbc3281000c58cd519fd640000',
        '7e14834bf13210009d25925272f40000',
        'ab822483adc710009d4b55d085e60000',
        '07564020a4451005a3027f2ca2d60000',
    ],
    'timeType': ['82babb82cec6011cb904bf090a820007'],
    'jobFamilyGroup': [
        '0cb9174e33c9100190f156427de80000',
        '0cb9174e33c91001910b070812780000',
    ],
    'workerSubType': ['07564020a4451005a308e94561c20000'],
}


@register_scraper
class BrowserStackScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.BROWSERSTACK

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
