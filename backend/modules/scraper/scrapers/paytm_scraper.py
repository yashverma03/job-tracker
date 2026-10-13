from modules.scraper.base.ripplehire_scraper import RippleHireScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

RIPPLEHIRE_HOST = 'paytm.ripplehire.com'
TOKEN = 'Jrn4GUz6HCYtOdlkVCzo'
ACCOUNT = 'Paytm'
COMPANY_NAME = 'Paytm'
SEARCH = 'software'
EXPERIENCE_YEARS = 3

@register_scraper
class PaytmScraper(RippleHireScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.PAYTM

    @property
    def ripplehire_host(self) -> str:
        return RIPPLEHIRE_HOST

    @property
    def token(self) -> str:
        return TOKEN

    @property
    def account(self) -> str:
        return ACCOUNT

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def search(self) -> str:
        return SEARCH

    @property
    def search_params(self) -> dict:
        return {'exp': EXPERIENCE_YEARS}
