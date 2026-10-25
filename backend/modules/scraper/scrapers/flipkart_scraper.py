from modules.scraper.base.turbohire_scraper import TurbohireScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'flipkart.turbohire.co'
ORG_ID = '4d757ba0-3d57-448a-b82c-238ed87ac90f'
COMPANY_NAME = 'Flipkart'


@register_scraper
class FlipkartScraper(TurbohireScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.FLIPKART

    @property
    def host(self) -> str:
        return HOST

    @property
    def org_id(self) -> str:
        return ORG_ID

    @property
    def company_name(self) -> str:
        return COMPANY_NAME
