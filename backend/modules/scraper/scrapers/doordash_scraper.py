from modules.scraper.base.greenhouse_scraper import GreenhouseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

BOARD_TOKEN = 'doordashindia'
COMPANY_NAME = 'DoorDash'
ALLOWED_DEPARTMENTS = {'341 executive engineering', '318 data'}


@register_scraper
class DoorDashScraper(GreenhouseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.DOORDASH

    @property
    def board_token(self) -> str:
        return BOARD_TOKEN

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def allowed_departments(self) -> set[str]:
        return ALLOWED_DEPARTMENTS
