from modules.scraper.services.scraper_pipeline_service import run_scraper_pipeline


def run_scraper_pipeline_task(
    scraper_names: list[str] | None,
    max_jobs_per_run: int,
    start_offset: int,
    time_range_hours: int,
    run_scoring: bool = False,
    init_only: bool = False,
) -> None:
    run_scraper_pipeline(scraper_names, max_jobs_per_run, start_offset, time_range_hours, run_scoring, init_only)
