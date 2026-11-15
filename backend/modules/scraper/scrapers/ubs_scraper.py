from modules.scraper.base.brassring_scraper import BrassringScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'jobs.ubs.com'
PARTNER_ID = '25008'
SITE_ID = '5012'
COMPANY_NAME = 'UBS'

FACET_FILTERS = {
    'formtext2': ['Hyderabad', 'Mumbai', 'Pune'],  # City
    'formtext21': [  # Function Category
        'Digital',
        'Information Technology (IT)',
        'Product management and development',
    ],
}
EXCLUDED_DESCRIPTION_LABELS = {'about us', 'join us', 'disclaimer / policy statements'}


@register_scraper
class UbsScraper(BrassringScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.UBS

    @property
    def host(self) -> str:
        return HOST

    @property
    def partner_id(self) -> str:
        return PARTNER_ID

    @property
    def site_id(self) -> str:
        return SITE_ID

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def facet_filters(self) -> dict[str, list[str]]:
        return FACET_FILTERS

    @property
    def excluded_description_labels(self) -> set[str]:
        return EXCLUDED_DESCRIPTION_LABELS
