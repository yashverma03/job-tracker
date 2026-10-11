from modules.scraper.base.oracle_cloud_hcm_scraper import OracleCloudHcmScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'egug.fa.us2.oraclecloud.com'
SITE_NUMBER = 'CX_1'
COMPANY_NAME = 'American Express'
JOB_URL_TEMPLATE = 'https://careers.americanexpress.com/en/sites/CX_1/job/{job_id}'

SELECTED_FLEX_FIELDS_FACETS = 'AttributeChar6|Technology'
SELECTED_LOCATIONS_FACET = '300000000228786'  # India
SELECTED_POSTING_DATES_FACET = '7'  # last 7 days


@register_scraper
class AmericanExpressScraper(OracleCloudHcmScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.AMERICAN_EXPRESS

    @property
    def host(self) -> str:
        return HOST

    @property
    def site_number(self) -> str:
        return SITE_NUMBER

    @property
    def company_name(self) -> str:
        return COMPANY_NAME

    @property
    def job_url_template(self) -> str:
        return JOB_URL_TEMPLATE

    @property
    def selected_flex_fields_facets(self) -> str | None:
        return SELECTED_FLEX_FIELDS_FACETS

    @property
    def selected_locations_facet(self) -> str | None:
        return SELECTED_LOCATIONS_FACET

    @property
    def selected_posting_dates_facet(self) -> str | None:
        return SELECTED_POSTING_DATES_FACET
