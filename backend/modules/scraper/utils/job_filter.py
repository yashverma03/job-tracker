from common.utils.text_normalizer import normalize_text

EXCLUDED_TITLE_WORDS: list[str] = [
    'manager',
    'principle',
    'principal',
    'lead',
    'architect',
    'firmware',
    'sde 3',
    'sde 4',
    'sde iii',
    'sde iv',
    'sde 3 developer',
    'sde 3 engineer',
    'sde 4 developer',
    'sde 4 engineer',
    'sde iii developer',
    'sde iii engineer',
    'sde iv developer',
    'sde iv engineer',
    'development engineer 3',
    'development engineer 4',
    'development engineer iii',
    'development engineer iv',
    'developer 3',
    'developer 4',
    'developer iii',
    'developer iv',
    'engineer 3',
    'engineer 4',
    'engineer iii',
    'engineer iv',
    'staff software',
    'staff developer',
    'staff engineer',
    '.net developer',
    '.net engineer',
    '.net software',
    'asp.net',
    'golang developer',
    'golang',
    'go developer',
    'c# developer',
    'c# engineer',
    'c++ developer',
    'c++ engineer',
    'rust',
    'ruby on rails',
    'ruby developer',
    'php',
    'laravel',
    'qa engineer',
    'qa',
    'Quality',
    'quality assurance',
    'sdet',
    'test',
    'embedded',
    'consultant',
    'consulting',
    'scala developer',
    'scala engineer',
    'mulesoft',
    'intern',
    'support engineer',
    'support developer',
    'customer engineer',
    'hardware',
    'cyber security',
    'blockchain',
    'ai research',
    'data scientist',
    'data analyst',
    'ml engineer',
    'Machine Learning Engineer',
    'MLOps',
    'AI Engineer',
    'devops engineer',
    'cloud engineer',
    'forward deployed',
    'solutions engineer',
    'founding engineer',
    'cto',
    'distinguished engineer',
    'associate vp',
    'vice president',
    'vp',
    'avp',
    'svp',
    'Scientist',
    'junior',
    'director',
    'leader',
    'leadership',
    'tester',
    'testing',
    'internship',
    'instructor',
    'teaching',
    'trainer',
    'apprentice',
    'partner',
    'Network Developer',
    'Network Engineer',
    'UI Developer',
    'Mgr',
    'Data Science Engineer',
    'frontend developer',
    'frontend engineer',
    'frontend software',
    'account executive',
    'business executive',
    'operation executive',
    'operations executive',
    'business development executive',
    'channel sales executive',
    'operation associate',
    'operations associate',
    'business associate',
    'business analyst',
    'business development',
    'sales development representative',
    'banking operation',
    'banking operations',
    'content marketing',
    'product sales',
    'product designer',
]

ALLOWED_LOCATION_SUBSTRINGS: list[str] = [
    'delhi',
    'new delhi',
    'ncr',
    'national capital region',
    'gurgaon',
    'gurugram',
    'noida',
    'greater noida',
    'bangalore',
    'bengaluru',
    'hyderabad',
    'secunderabad',
    'pune',
    'chennai',
    'madras',
    'mumbai',
    'navi mumbai',
    'bombay',
    'remote',
    'location',
    'unknown',
]

# Only an exact "India" (no city specified) is in scope, not any location that merely
# contains "India" (e.g. "West Bengal, India"). "NA"/"N/A" is matched the same way -
# exact (the whole, word-tokenized location), never a substring - since as a raw
# substring it falsely matches inside unrelated words (e.g. "Canada", "National").
EXACT_ALLOWED_LOCATIONS: list[str] = [
    'india',
    'na',
]


def _words(text: str) -> list[str]:
    return normalize_text(text, ' ').strip().split(' ')


def _contains_phrase(words: list[str], phrase: str) -> bool:
    phrase_words = _words(phrase)
    phrase_len = len(phrase_words)
    return any(words[start : start + phrase_len] == phrase_words for start in range(len(words) - phrase_len + 1))


def is_title_excluded(title: str | None) -> bool:
    if not title:
        return False

    title_words = _words(title)
    if title_words == ['']:
        return False

    return any(_contains_phrase(title_words, word) for word in EXCLUDED_TITLE_WORDS)


def is_location_excluded(location: str | None) -> bool:
    if not location:
        return False

    location_words = _words(location)
    if location_words == ['']:
        return False

    if location_words in (_words(allowed) for allowed in EXACT_ALLOWED_LOCATIONS):
        return False

    return not any(_contains_phrase(location_words, city) for city in ALLOWED_LOCATION_SUBSTRINGS)
