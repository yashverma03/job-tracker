import json
import re

from bs4 import BeautifulSoup

from common.utils.http import get_with_retry

RSC_REQUEST_HEADER = {'RSC': '1'}
NEXT_F_PUSH_CALL_PATTERN = re.compile(r'self\.__next_f\.push\(\[\d+,(".*)\]\)\s*$', re.S)


def fetch_rsc_payload(get_session, url: str, **kwargs) -> str:
    """Fetches a Next.js (App Router) page's React Flight ("RSC") payload directly, the
    same way Next.js's own client-side router fetches it for a navigation: a plain GET
    with an `RSC: 1` request header. This returns just the flight-format text body
    (smaller than the full HTML page, and avoids the build-id-scoped `_rsc=<id>` query
    param some sites' URLs expose, which goes stale across deployments) - not a parsed
    object, since the payload isn't plain JSON (see `extract_json_value`)."""
    headers = {**RSC_REQUEST_HEADER, **kwargs.pop('headers', {})}
    response = get_with_retry(get_session, url, headers=headers, **kwargs)
    response.raise_for_status()
    return response.text


def decode_next_f_stream(html: str) -> str:
    """Fallback for when a full HTML page (not a direct RSC-header fetch) is all
    that's available: concatenates every React Flight string chunk Next.js streamed
    into the page, each as its own `<script>self.__next_f.push([id, "<json-escaped
    chunk>"])</script>` tag, into one string, so a value can then be located in it
    with `extract_json_value`. Uses BeautifulSoup to isolate each script tag's own
    text rather than regex-scanning the whole raw HTML, so the match can't run past
    its own tag's boundary."""
    decoded_parts = []
    for script in BeautifulSoup(html, 'html.parser').find_all('script'):
        match = NEXT_F_PUSH_CALL_PATTERN.search(script.string or '')
        if match is None:
            continue
        try:
            decoded_parts.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return ''.join(decoded_parts)


def extract_json_value(payload: str, key: str, start: int = 0, expected_type: type | None = None):
    """Finds `"<key>":` in a decoded RSC/React-Flight payload and bracket-matches the
    JSON value that follows it, via `json.JSONDecoder().raw_decode` rather than a
    regex - a regex can't safely bound a value containing nested brackets/quotes (e.g.
    a job title). The same key can legitimately appear more than once in a payload
    (e.g. once in a translation-strings object, once as the actual field a caller
    wants) with differently-shaped values, so pass `expected_type` (`list`, `dict`,
    ...) to skip occurrences whose value doesn't match it. Returns `(value,
    end_index)`, where `end_index` lets a caller keep scanning the remainder of the
    payload for other keys (e.g. pagination metadata following a listing array);
    returns `(None, -1)` if no matching occurrence of `key` is found at or after
    `start`."""
    marker = f'"{key}":'
    search_from = start
    while True:
        index = payload.find(marker, search_from)
        if index == -1:
            return None, -1
        value, end_index = json.JSONDecoder().raw_decode(payload, index + len(marker))
        if expected_type is None or isinstance(value, expected_type):
            return value, end_index
        search_from = index + len(marker)
