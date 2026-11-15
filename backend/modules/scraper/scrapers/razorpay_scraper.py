from modules.scraper.base.greenhouse_scraper import GreenhouseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

BOARD_TOKEN = 'razorpaysoftwareprivatelimited'
COMPANY_NAME = 'Razorpay'
# Engineering plus its child department (DevOps), matching the board's own department filter
ALLOWED_DEPARTMENTS = {'engineering', 'devops'}


@register_scraper
class RazorpayScraper(GreenhouseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.RAZORPAY

    @property
    def board_token(self) -> str:
        return BOARD_TOKEN

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def allowed_departments(self) -> set[str]:
        return ALLOWED_DEPARTMENTS
