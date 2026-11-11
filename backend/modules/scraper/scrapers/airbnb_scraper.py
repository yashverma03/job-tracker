from modules.scraper.base.greenhouse_scraper import GreenhouseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

BOARD_TOKEN = 'airbnb'
COMPANY_NAME = 'Airbnb'
ALLOWED_COUNTRIES = {'india'}
ALLOWED_DEPARTMENTS = {'software engineering', 'engineering & technology'}


@register_scraper
class AirbnbScraper(GreenhouseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.AIRBNB

    @property
    def board_token(self) -> str:
        return BOARD_TOKEN

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def allowed_countries(self) -> set[str]:
        return ALLOWED_COUNTRIES

    @property
    def allowed_departments(self) -> set[str]:
        return ALLOWED_DEPARTMENTS
