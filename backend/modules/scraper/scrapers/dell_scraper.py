from modules.scraper.base.oracle_cloud_hcm_scraper import OracleCloudHcmScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper

HOST = 'enterpriseplatform.dell.com'
SITE_NUMBER = 'CX_1001'
COMPANY_NAME = 'Dell'
JOB_URL_TEMPLATE = 'https://enterpriseplatform.dell.com/hcmUI/CandidateExperience/en/sites/careers/job/{job_id}'

SELECTED_LOCATIONS_FACET = '300000000471053'  # India
SELECTED_TITLES_FACET = 'DATA SCIENCE & ANALYTICS;INFORMATION TECHNOLOGY;ENGREDEV;PROFESSIONAL SERVICES'
SELECTED_POSTING_DATES_FACET = '30'  # Less than 30 days


@register_scraper
class DellScraper(OracleCloudHcmScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.DELL

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
