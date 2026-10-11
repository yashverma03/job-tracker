from modules.scraper.base.smart_recruiters_scraper import SmartRecruitersScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

COMPANY_IDENTIFIER = 'PHONEPELIMITED'
COMPANY_NAME = 'PhonePe'

# PhonePe's "Department Name" custom field.
DEPARTMENT_NAME_FIELD_ID = '6a7d92cd2e46562183ed41eb'
DEPARTMENT_NAME_VALUES = [
    '15328470',  # Engineering
    '15328471',  # Tech Infra & IT
    '15328474',  # Analytics
]


@register_scraper
class PhonePeScraper(SmartRecruitersScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.PHONEPE

    @property
    def company_identifier(self) -> str:
        return COMPANY_IDENTIFIER

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def search_params(self) -> dict:
        return {f'custom_field.{DEPARTMENT_NAME_FIELD_ID}': DEPARTMENT_NAME_VALUES}
