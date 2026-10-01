from modules.scraper.base.workday_scraper import WorkdayScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

WORKDAY_HOST = 'barclays.wd3.myworkdayjobs.com'
TENANT = 'barclays'
SITE = 'External_Career_Site_Barclays'
COMPANY_NAME = 'Barclays'
PAGE_SIZE = 20

APPLIED_FACETS = {
    'jobFamilyGroup': ['112c054282011001e9162cfccdc10000'],  # Technology
    'locations': [
        '1110a9ca6540100196e1f0c315e90000',  # Bengaluru, Maruthi Onyx - TESCO TSA
        '112c05428201100163788a5627320000',  # Chennai, DLF IT Park
        '253dfca5ccfc10016b1361f46cfe0000',  # Gurugram, DLF Downtown
        '112c0542820110016378a0a3e68d0000',  # Ceejay House, Mumbai
        'b8f75d1cb9781000cd91027a85e30000',  # Mumbai, Nirlon Knowledge Park (BX)
        '1ab48a98eb7c100163423aff71b80000',  # Mumbai, Nirlon Knowledge Park (IB)
        '112c0542820110016377af553b050000',  # New Delhi, Eros Corporate Tower
        '112c0542820110016377c02c6ef00000',  # Noida, Candor TechSpace
        '112c05428201100163763bd6ad400000',  # Pune, Gera Commerzone SEZ
    ],
}


@register_scraper
class BarclaysScraper(WorkdayScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.BARCLAYS

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

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
