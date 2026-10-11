from modules.scraper.base.oracle_cloud_hcm_scraper import OracleCloudHcmScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'eeho.fa.us2.oraclecloud.com'
SITE_NUMBER = 'CX_45001'
COMPANY_NAME = 'Oracle'
JOB_URL_TEMPLATE = 'https://careers.oracle.com/en/sites/jobsearch/job/{job_id}'

SELECTED_FLEX_FIELDS_FACETS = 'AttributeChar4|Employee||AttributeChar29|Individual Contributor||AttributeChar6|3 to 5+ years'
SELECTED_LOCATIONS_FACET = '300000000106947'
SELECTED_POSTING_DATES_FACET = '2'


@register_scraper
class OracleScraper(OracleCloudHcmScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.ORACLE

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
