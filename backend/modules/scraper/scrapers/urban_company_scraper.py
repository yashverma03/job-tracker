from modules.scraper.base.turbohire_scraper import TurbohireScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'urbancompany.turbohire.co'
ORG_ID = '4ea15045-6e8b-4edf-8274-899578e56a56'
COMPANY_NAME = 'Urban Company'


@register_scraper
class UrbanCompanyScraper(TurbohireScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.URBAN_COMPANY

    @property
    def host(self) -> str:
        return HOST

    @property
    def org_id(self) -> str:
        return ORG_ID

    @property
    def company_name(self) -> str:
        return COMPANY_NAME
