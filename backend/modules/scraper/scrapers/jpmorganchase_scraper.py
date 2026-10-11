from modules.scraper.base.oracle_cloud_hcm_scraper import OracleCloudHcmScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'jpmc.fa.oraclecloud.com'
SITE_NUMBER = 'CX_1001'
COMPANY_NAME = 'JPMorganChase'
JOB_URL_TEMPLATE = 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}'

SELECTED_LOCATIONS_FACET = '300000000289360'  # India (country-level)
SELECTED_CATEGORIES_FACET = '300000086152753'  # Software Engineering
SELECTED_POSTING_DATES_FACET = '2'


@register_scraper
class JpMorganChaseScraper(OracleCloudHcmScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.JPMORGANCHASE

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
    def selected_categories_facet(self) -> str | None:
        return SELECTED_CATEGORIES_FACET

    @property
    def selected_posting_dates_facet(self) -> str | None:
        return SELECTED_POSTING_DATES_FACET
