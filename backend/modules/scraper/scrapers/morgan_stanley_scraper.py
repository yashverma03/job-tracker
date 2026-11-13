from modules.scraper.base.eightfold_scraper import EightfoldScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

COMPANY_NAME = 'Morgan Stanley'
DOMAIN = 'morganstanley.com'
HOST = 'morganstanley.eightfold.ai'

EXTRA_FILTERS = {
    'businessarea': ['technology', 'technology and operations'],
    'pcsjoblevel': ['professional'],
    'country': ['India', 'Singapore'],
}


@register_scraper
class MorganStanleyScraper(EightfoldScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.MORGAN_STANLEY

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
    def location(self) -> str:
        return ''

    @property
    def include_remote(self) -> bool:
        return False

    @property
    def extra_filters(self) -> dict[str, list[str]]:
        return EXTRA_FILTERS
