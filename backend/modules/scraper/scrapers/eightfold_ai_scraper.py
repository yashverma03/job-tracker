from modules.scraper.base.eightfold_scraper import EightfoldScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

COMPANY_NAME = 'Eightfold AI'
DOMAIN = 'eightfold.ai'


@register_scraper
class EightfoldAiScraper(EightfoldScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.EIGHTFOLD_AI

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def domain(self) -> str:
        return DOMAIN

    @property
    def departments(self) -> list[str]:
        return ['Engineering']

    @property
    def seniority_levels(self) -> list[str]:
        return ['1', '2']
