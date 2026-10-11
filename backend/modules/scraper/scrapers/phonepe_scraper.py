from modules.scraper.base.smart_recruiters_scraper import SmartRecruitersScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

COMPANY_IDENTIFIER = 'PHONEPELIMITED'
COMPANY_NAME = 'PhonePe'


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
