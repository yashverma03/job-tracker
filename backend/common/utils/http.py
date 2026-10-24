from curl_cffi.requests.exceptions import HTTPError, RequestException
from tenacity import RetryError, retry, retry_if_exception_type, retry_if_result, stop_after_attempt, wait_exponential

RETRYABLE_STATUS_CODES = {429, 999}
MAX_GET_RETRIES = 3

# 429/999 blocks don't clear in a few seconds, so back off 10s, 20s, 40s between attempts.
RETRY_WAIT_MULTIPLIER_SECONDS = 10
RETRY_MIN_WAIT_SECONDS = 10
RETRY_MAX_WAIT_SECONDS = 60
_RETRY_WAIT = wait_exponential(
    multiplier=RETRY_WAIT_MULTIPLIER_SECONDS, min=RETRY_MIN_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS
)

# Kept short so a large HTML error/challenge page doesn't blow up the log line.
RETRY_ERROR_BODY_LIMIT = 500

_STATUS_HINTS = {
    429: 'rate limited (too many requests)',
    999: 'blocked by anti-bot protection',
}


class RetryExhaustedError(HTTPError):
    """An HTTPError whose message already includes the status and response body."""


def _retry_exhausted_error(method: str, url: str, exc: RetryError) -> RetryExhaustedError:
    """tenacity raises a bare `RetryError` when the last attempt still returned a
    retryable *response* (reraise only applies to exceptions), which says nothing about
    what went wrong. Re-raise it as an `HTTPError` carrying the last response, so
    callers' existing HTTPError handling reports the status and body."""
    response = exc.last_attempt.result()
    status_code = response.status_code
    hint = _STATUS_HINTS.get(status_code, 'server error' if status_code >= 500 else 'retryable status')
    body = (response.text or '')[:RETRY_ERROR_BODY_LIMIT]
    message = (
        f'{method} {url} failed after {MAX_GET_RETRIES + 1} attempts: HTTP {status_code} ({hint}); '
        f'last response body={body!r}'
    )
    return RetryExhaustedError(message, response=response)


def _is_retryable_response(response) -> bool:
    return response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 500


def get_with_retry(get_session, url, on_retry=None, **kwargs):
    """GET via a session, retrying on 429/999/5xx responses and any request exception (connection
    errors, SSL errors, timeouts, etc. - curl_cffi raises all of these as subclasses of
    RequestException).
   """

    @retry(
        retry=(retry_if_result(_is_retryable_response) | retry_if_exception_type(RequestException)),
        stop=stop_after_attempt(MAX_GET_RETRIES + 1),
        wait=_RETRY_WAIT,
        before_sleep=(lambda *_: on_retry()) if on_retry is not None else None,
        reraise=True,
    )
    def _do_request():
        return get_session().get(url, **kwargs)

    try:
        return _do_request()
    except RetryError as exc:
        raise _retry_exhausted_error('GET', url, exc) from exc


def post_with_retry(get_session, url, on_retry=None, **kwargs):
    """Same retry behavior as `get_with_retry`, for APIs (e.g. Workday) whose list
    endpoint only accepts POST with a JSON body."""

    @retry(
        retry=(retry_if_result(_is_retryable_response) | retry_if_exception_type(RequestException)),
        stop=stop_after_attempt(MAX_GET_RETRIES + 1),
        wait=_RETRY_WAIT,
        before_sleep=(lambda *_: on_retry()) if on_retry is not None else None,
        reraise=True,
    )
    def _do_request():
        return get_session().post(url, **kwargs)

    try:
        return _do_request()
    except RetryError as exc:
        raise _retry_exhausted_error('POST', url, exc) from exc
