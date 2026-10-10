from modules.scraper.base.oracle_cloud_hcm_scraper import OracleCloudHcmScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'fa-extu-saasfaprod1.fa.ocs.oraclecloud.com'
SITE_NUMBER = 'CX_1'
COMPANY_NAME = 'Akamai'
JOB_URL_TEMPLATE = 'https://jobs.akamai.com/en/sites/CX_1/job/{job_id}'
PAGE_SIZE = 25

SELECTED_LOCATIONS_FACET = '300000000469285'  # India
SELECTED_TITLES_FACET = 'ENG'  # Engineering


@register_scraper
class AkamaiScraper(OracleCloudHcmScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.AKAMAI

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

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
    def selected_locations_facet(self) -> str | None:
        return SELECTED_LOCATIONS_FACET

    @property
    def selected_titles_facet(self) -> str | None:
        return SELECTED_TITLES_FACET
