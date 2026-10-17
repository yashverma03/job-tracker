from modules.scraper.base.beesite_scraper import BeesiteScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'api-deutschebank.beesite.de'
COMPANY_NAME = 'Deutsche Bank'
JOB_URL_TEMPLATE = 'https://careers.db.com/professionals/search-roles/#/professional/job/{position_id}'

INDIA_COUNTRY_CODE = '81'
ENGINEERING_PROFESSION_CATEGORY_CODE = '1328'
ENGINEERING_PROFESSION_CODE = '1330'

SEARCH_CRITERIA = [
    {'CriterionName': 'PositionLocation.Country', 'CriterionValue': [INDIA_COUNTRY_CODE]},
    {'CriterionName': 'ProfessionCategory.Code', 'CriterionValue': [ENGINEERING_PROFESSION_CATEGORY_CODE]},
    {'CriterionName': 'Profession.Code', 'CriterionValue': [ENGINEERING_PROFESSION_CODE]},
]


@register_scraper
class DeutscheBankScraper(BeesiteScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.DEUTSCHE_BANK

    @property
    def host(self) -> str:
        return HOST

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def job_url_template(self) -> str:
        return JOB_URL_TEMPLATE

    @property
    def search_criteria(self) -> list[dict]:
        return SEARCH_CRITERIA
