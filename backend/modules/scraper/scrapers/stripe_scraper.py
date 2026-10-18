from modules.scraper.base.greenhouse_scraper import GreenhouseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

BOARD_TOKEN = 'stripe'
COMPANY_NAME = 'Stripe'


@register_scraper
class StripeScraper(GreenhouseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.STRIPE

    @property
    def board_token(self) -> str:
        return BOARD_TOKEN

    @property
    def company_name(self) -> str:
        return COMPANY_NAME
