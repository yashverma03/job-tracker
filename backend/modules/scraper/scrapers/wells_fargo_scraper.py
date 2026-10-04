from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'wf.wd1.myworkdayjobs.com'
TENANT = 'wf'
SITE = 'WellsFargoJobs'
COMPANY_NAME = 'Wells Fargo'

APPLIED_FACETS = {
    'jobFamily': [
        '6cee717ed86e0100b325200f972a0001',  # Technology Engineering
        '6cee717ed86e0100b32520aa42290002',  # Technology Operations
        'c552daa57e621001a3012862ce310000',  # Architecture
        '6cee717ed86e0100b32520aa42290000',  # Technology Enablement
        '1018d766e49a1001be3a1fcd33700000',  # Advanced Analytics
        '6cee717ed86e0100b32506af913b0000',  # Analytics
        'aa461b8bce6b1001be47390fa4fd0000',  # Data Management & Product
        '6cee717ed86e0100b3251f75aca70001',  # Information Security Operations
    ],
    'workerSubType': ['2d264dd4beb00100f05a7cc5745b0001'],  # Regular
    'timeType': ['50c5418d15190102da8c58e585d90001'],  # Full time
    'locationCountry': ['c4f78be1a8f14da0ab49ce1162348a5e'],  # India
}


@register_scraper
class WellsFargoScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.WELLS_FARGO

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
