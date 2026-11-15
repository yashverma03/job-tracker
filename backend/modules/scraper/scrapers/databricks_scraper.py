from modules.scraper.base.greenhouse_scraper import GreenhouseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

BOARD_TOKEN = 'databricks'
COMPANY_NAME = 'Databricks'
ALLOWED_COUNTRIES = {'india'}
# Greenhouse departments behind the careers site's "Engineering" and "IT" filter groups
ALLOWED_DEPARTMENTS = {
    'engineering',
    'engineering - pipeline',
    'executive engineering - pipeline',
    'infrastructure',
    'integration, data, engineering and applications',
}


@register_scraper
class DatabricksScraper(GreenhouseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.DATABRICKS

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
