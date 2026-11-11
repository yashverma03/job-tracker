from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'salesforce.wd12.myworkdayjobs.com'
TENANT = 'salesforce'
SITE = 'External_Career_Site'
COMPANY_NAME = 'Salesforce'

APPLIED_FACETS = {
    'CF_-_REC_-_LRV_-_Job_Posting_Anchor_-_Country_from_Job_Posting_Location_Extended': [
        'c4f78be1a8f14da0ab49ce1162348a5e',  # India
    ],
    'jobFamilyGroup': [
        '14fa3452ec7c1011f90d0002a2100000',  # Software Engineering
        '14fa3452ec7c1011f90cf661a7c80000',  # Data
        '14fa3452ec7c1011f90cf8c9c5960000',  # Enterprise Technology & Infrastructure
        '14fa3452ec7c1011f90cf3f9543c0000',  # Development & Strategy
    ],
}


@register_scraper
class SalesforceScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.SALESFORCE

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
