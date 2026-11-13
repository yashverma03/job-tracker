from modules.scraper.base.eightfold_scraper import EightfoldScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

COMPANY_NAME = 'PayPal'
DOMAIN = 'paypal.com'
HOST = 'paypal.eightfold.ai'


@register_scraper
class PaypalScraper(EightfoldScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.PAYPAL

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def domain(self) -> str:
        return DOMAIN

    @property
    def host(self) -> str:
        return HOST

    @property
    def job_categories(self) -> list[str]:
        return ['Software Engineering', 'Cybersecurity Engineering']
