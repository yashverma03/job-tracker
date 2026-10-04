from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'ag.wd3.myworkdayjobs.com'
TENANT = 'ag'
SITE = 'Airbus'
COMPANY_NAME = 'Airbus'

APPLIED_FACETS = {
    'locationCountry': ['c4f78be1a8f14da0ab49ce1162348a5e'],  # India
    'jobFamilyGroup': [
        'f5811cef9cb5018463377f3f550a1bf2',  # Engineering <FU-EN>
        'f5811cef9cb5015323ad7f3f550a1df2',  # Digital <FU-IM>
    ],
    'workerSubType': ['f5811cef9cb501a69768a71d470a6d15'],  # Regular
    'FullPartTime': ['70a157281071017ad8c0ee4170448100'],  # Full time
    'jobFamily': [
        'f5811cef9cb501602cf214e9540adaec',  # Digital <JF-IM-DI>
        'f5811cef9cb5018f6f641ee9540a16ed',  # Software Engineering <JF-EN-EK>
    ],
    'startDate': [
        '29d7affdc34a10001f8fca3a631900f8',  # Posted within 1 Week
    ],
}


@register_scraper
class AirbusScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.AIRBUS

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
