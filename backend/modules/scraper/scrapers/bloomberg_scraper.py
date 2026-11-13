from modules.scraper.base.avature_scraper import AvatureScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

SEARCH_PARAMS = {
    '1845': '[162477,162575]',  # Location: Mumbai, Pune
    '1845_format': 3996,  # filter widget type, always sent alongside its field
    '1686': '[55478,57029]',  # Experience Level: Early Careers, Experienced
    '1686_format': 2312,
    '2562': '[219293,219290,219309]',  # Business Area: Data, Engineering and CTO, Product
    '2562_format': 6594,
    'listFilterMode': 1,  # apply the filters above (1 = filtered search)
}


@register_scraper
class BloombergScraper(AvatureScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.BLOOMBERG

    @property
    def host(self) -> str:
        return 'bloomberg.avature.net'

    @property
    def company_name(self) -> str:
        return 'Bloomberg'

    @property
    def search_params(self) -> dict:
        return SEARCH_PARAMS
