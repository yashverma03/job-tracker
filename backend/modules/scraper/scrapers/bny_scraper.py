from modules.scraper.base.oracle_cloud_hcm_scraper import OracleCloudHcmScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'eofe.fa.us2.oraclecloud.com'
SITE_NUMBER = 'CX_3001'
COMPANY_NAME = 'BNY Mellon'
JOB_URL_TEMPLATE = 'https://eofe.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/BNY-Careers/job/{job_id}'

SELECTED_LOCATIONS_FACET = '300000000378365'  # India
SELECTED_TITLES_FACET = 'SOENG'  # Software Engineering
SELECTED_POSTING_DATES_FACET = '7'


@register_scraper
class BnyScraper(OracleCloudHcmScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.BNY_MELLON

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

    @property
    def selected_posting_dates_facet(self) -> str | None:
        return SELECTED_POSTING_DATES_FACET
