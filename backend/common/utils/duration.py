def format_duration(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f'{hours} hr')
    if minutes:
        parts.append(f'{minutes} min')
    if secs or not parts:
        parts.append(f'{secs} sec')
    return ' '.join(parts)
