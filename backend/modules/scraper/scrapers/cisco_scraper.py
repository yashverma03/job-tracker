from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'cisco.wd5.myworkdayjobs.com'
TENANT = 'cisco'
SITE = 'Cisco_Careers'
COMPANY_NAME = 'Cisco'

APPLIED_FACETS = {
    'jobFamilyGroup': [
        '2101eee3ea96016aef42a674fc016429',  # Engineering
        '2101eee3ea96017b1ceba674fc016829',  # Information Technology
    ],
    'workerSubType': ['a5e1942e7b2c01f937db30106001b800'],  # Regular
    'timeType': ['672880041e5001a878ea77353f075800'],  # Full time
    'locations': [
        '662e524adea41001f4d0bd5a1ddd0000',  # Bangalore, India
        '3dbd26f9e73e1001f4d59df763f20000',  # Chennai, India
        '026fa05becb01001f506953e0df00000',  # Gurgaon, India
        'ef8a5a22403d1001f4fde228ba110000',  # Hyderabad, India
        '6bed8334bf4b1001f4f15a1f787a0000',  # Mumbai, India
        '8676de3331b41001f4f96625fdde0000',  # New Delhi, India
        '8676de3331b41001f4eaac80a6280000',  # Pune, India
    ],
}


@register_scraper
class CiscoScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.CISCO

    @property
    def workday_host(self) -> str:
        return WORKDAY_HOST

    @property
    def tenant(self) -> str:
        return TENANT

    @property
    def site(self) -> str:
        return SITE

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def applied_facets(self) -> dict:
        return APPLIED_FACETS
