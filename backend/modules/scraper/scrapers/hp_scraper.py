from modules.scraper.base.eightfold_scraper import EightfoldScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'apply.hp.com'
COMPANY_NAME = 'HP'
DOMAIN = 'hp.com'

JOB_CATEGORIES = [
    'data & information technology',
    'software',
    'engineering',
    'services',
    'technical',
    'engineering services',
]
SENIORITY_LEVELS = ['graduate', 'experienced']


@register_scraper
class HpScraper(EightfoldScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.HP

    @property
    def host(self) -> str:
        return HOST

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def domain(self) -> str:
        return DOMAIN

    @property
    def job_categories(self) -> list[str]:
        return JOB_CATEGORIES

    @property
    def seniority_levels(self) -> list[str]:
        return SENIORITY_LEVELS
