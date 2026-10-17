from modules.scraper.base.happydance_scraper import HappydanceScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'jobs.sap.com'
COMPANY_NAME = 'SAP'
SEARCH_PARAMS = {'team': ['Engineering', 'Information Technology'], 'country': ['India']}


@register_scraper
class SAPScraper(HappydanceScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.SAP

    @property
    def host(self) -> str:
        return HOST

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def search_params(self) -> dict:
        return SEARCH_PARAMS
