"""Expression engine for back-of-the-envelope estimations.

Parses informal math like "30 billion * 500 bytes" and returns
human-friendly results like "15 TB".
"""

from __future__ import annotations

import re
from typing import Optional

import pint

ureg = pint.UnitRegistry()
# Define month = 30 days for system design convention (pint's default is 1/12 Julian year)
ureg.define('month = 30 * day')

# --- Preprocessing ---

# Word multipliers: "30 billion" -> "30 * 1e9"
_WORD_MULTIPLIERS = [
    (re.compile(r'(\d+(?:\.\d+)?)\s+trillion', re.IGNORECASE), r'\1 * 1e12'),
    (re.compile(r'(\d+(?:\.\d+)?)\s+billion', re.IGNORECASE), r'\1 * 1e9'),
    (re.compile(r'(\d+(?:\.\d+)?)\s+million', re.IGNORECASE), r'\1 * 1e6'),
    (re.compile(r'(\d+(?:\.\d+)?)\s+thousand', re.IGNORECASE), r'\1 * 1e3'),
]

# Suffix multipliers: "20K" -> "20e3", "30B" -> "30e9"
# Negative lookahead prevents matching "bytes", "MB", etc.
_SUFFIX_MULTIPLIERS = [
    (re.compile(r'(\d+(?:\.\d+)?)\s*T(?![a-zA-Z])'), r'\1e12'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*B(?![a-zA-Z])'), r'\1e9'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*M(?![a-zA-Z])'), r'\1e6'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*K(?![a-zA-Z])'), r'\1e3'),
]

# Known data-size unit tokens (case-insensitive matching) -> pint unit name
_BYTE_UNITS = {
    'bytes': 'byte', 'byte': 'byte',
    'kb': 'kilobyte', 'kilobyte': 'kilobyte', 'kilobytes': 'kilobyte',
    'mb': 'megabyte', 'megabyte': 'megabyte', 'megabytes': 'megabyte',
    'gb': 'gigabyte', 'gigabyte': 'gigabyte', 'gigabytes': 'gigabyte',
    'tb': 'terabyte', 'terabyte': 'terabyte', 'terabytes': 'terabyte',
    'pb': 'petabyte', 'petabyte': 'petabyte', 'petabytes': 'petabyte',
}

# Known time unit tokens (appear after "/") -> pint unit name
_TIME_UNITS = {
    'second': 'second', 'seconds': 'second', 's': 'second',
    'minute': 'minute', 'minutes': 'minute', 'min': 'minute',
    'hour': 'hour', 'hours': 'hour', 'hr': 'hour',
    'day': 'day', 'days': 'day',
    'month': 'month', 'months': 'month',
    'year': 'year', 'years': 'year',
}

# Rate dropdown -> pint time unit name
_RATE_UNITS = {
    "none": None,
    "/s": "second", "/min": "minute", "/hour": "hour",
    "/day": "day", "/month": "month", "/year": "year",
}

# Allowed chars in the math portion after unit stripping
_SAFE_MATH_RE = re.compile(r'^[\d\s\.\+\-\*\/\(\)eE]+$')


def _preprocess_scale(expr: str) -> str:
    """Replace human-friendly multiplier words/suffixes with numeric equivalents."""
    s = expr.strip()
    for pattern, repl in _WORD_MULTIPLIERS:
        s = pattern.sub(repl, s)
    for pattern, repl in _SUFFIX_MULTIPLIERS:
        s = pattern.sub(repl, s)
    return s


def _parse_units(expr: str) -> tuple[str, Optional[str], Optional[str]]:
    """Extract data unit and time divisor unit from expression.

    Returns (math_str, data_pint_unit_or_None, time_pint_unit_or_None).
    """
    data_unit = None
    time_unit = None
    math_str = expr

    # Check for time divisor: "/ month", "/ day", "/ second", etc.
    time_match = re.search(r'/\s*([a-zA-Z]+)\s*$', math_str)
    if time_match:
        token = time_match.group(1).lower()
        if token in _TIME_UNITS:
            time_unit = _TIME_UNITS[token]
            math_str = math_str[:time_match.start()].strip()

    # Check for data unit token at end of remaining expression
    tokens = math_str.strip().split()
    if tokens:
        last = tokens[-1].lower()
        if last in _BYTE_UNITS:
            data_unit = _BYTE_UNITS[last]
            math_str = ' '.join(tokens[:-1]).rstrip(' *')

    return math_str, data_unit, time_unit


def _safe_eval(math_str: str) -> float:
    """Evaluate a math string after safety validation."""
    cleaned = math_str.strip()
    if not cleaned:
        raise ValueError("Empty expression")
    if not _SAFE_MATH_RE.match(cleaned):
        raise ValueError(f"Invalid characters in expression: {cleaned}")
    return float(eval(cleaned, {"__builtins__": {}}, {}))


# --- Auto-formatting ---

_BYTE_THRESHOLDS = [
    (1e15, 'petabyte', 'PB'),
    (1e12, 'terabyte', 'TB'),
    (1e9, 'gigabyte', 'GB'),
    (1e6, 'megabyte', 'MB'),
    (1e3, 'kilobyte', 'KB'),
    (1, 'byte', 'bytes'),
]

_NUMBER_THRESHOLDS = [
    (1e12, 'trillion'),
    (1e9, 'billion'),
    (1e6, 'million'),
    (1e3, 'K'),
]

def _format_number(value: float, rate: str = "") -> str:
    """Format a dimensionless number with human-readable suffix."""
    abs_val = abs(value)
    for threshold, suffix in _NUMBER_THRESHOLDS:
        if abs_val >= threshold:
            scaled = value / threshold
            formatted = _format_magnitude(scaled)
            # No space before short suffixes like K, space before words
            sep = "" if len(suffix) <= 1 else " "
            return f"{formatted}{sep}{suffix}{rate}"
    return f"{_format_magnitude(value)}{rate}"


def _format_magnitude(value: float) -> str:
    """Format a number nicely: ~1.7, 15, 100, ~193, etc."""
    if value == 0:
        return "0"
    rounded_int = round(value)
    rounded_1dp = round(value, 1)
    # If close to an integer (within 5%), show as integer
    if rounded_int != 0 and abs(value - rounded_int) / abs(rounded_int) < 0.05:
        if value == rounded_int or abs(value - rounded_int) < 0.01:
            return str(rounded_int)
        else:
            return f"~{rounded_int}"
    else:
        return f"~{rounded_1dp:g}"


# --- Public API ---

def evaluate(expression: str, target_unit: str = "auto", rate: str = "none") -> dict:
    """Evaluate an expression and return formatted result.

    Args:
        expression: e.g. "30 billion * 500 bytes", "500 million / month"
        target_unit: "auto", "bytes", "KB", "MB", "GB", "TB", "PB", or "none"
        rate: "none", "/s", "/min", "/hour", "/day", "/month", "/year"

    Returns:
        dict with keys: expression, result_display, raw_value
    """
    processed = _preprocess_scale(expression)
    math_str, data_unit, time_unit = _parse_units(processed)
    magnitude = _safe_eval(math_str)

    rate_time_unit = _RATE_UNITS.get(rate)
    rate_label = "" if rate == "none" else rate

    # Build pint quantity
    if data_unit and time_unit:
        quantity = magnitude * ureg(data_unit) / ureg(time_unit)
    elif data_unit:
        quantity = magnitude * ureg(data_unit)
    elif time_unit:
        quantity = magnitude / ureg(time_unit)
    else:
        quantity = None  # pure number

    # Convert and format
    if quantity is not None and time_unit and rate_time_unit:
        # Expression has time divisor AND user selected a rate → use pint to convert
        if data_unit:
            # byte/time → convert to best_byte_unit / target_time
            byte_mag = quantity.to(ureg.byte / ureg(rate_time_unit)).magnitude
            abs_val = abs(byte_mag)
            for threshold, pint_unit, display_label in _BYTE_THRESHOLDS:
                if abs_val >= threshold:
                    converted = ureg.Quantity(byte_mag, 'byte').to(pint_unit).magnitude
                    display = f"{_format_magnitude(converted)} {display_label}{rate_label}"
                    break
            else:
                display = f"{_format_magnitude(byte_mag)} bytes{rate_label}"
        else:
            # dimensionless/time → convert to 1/target_time
            per_rate = quantity.to(1 / ureg(rate_time_unit)).magnitude
            display = _format_number(per_rate, rate_label)
    elif quantity is not None and data_unit:
        # Byte quantity, no time conversion needed
        value_in_bytes = quantity.to('byte').magnitude
        if target_unit not in ("auto", "none"):
            pint_target = _BYTE_UNITS.get(target_unit.lower())
            if not pint_target:
                raise ValueError(f"Unknown target unit: {target_unit}")
            converted = ureg.Quantity(value_in_bytes, 'byte').to(pint_target).magnitude
            display = f"{_format_magnitude(converted)} {target_unit}{rate_label}"
        else:
            abs_val = abs(value_in_bytes)
            for threshold, pint_unit, display_label in _BYTE_THRESHOLDS:
                if abs_val >= threshold:
                    converted = ureg.Quantity(value_in_bytes, 'byte').to(pint_unit).magnitude
                    display = f"{_format_magnitude(converted)} {display_label}{rate_label}"
                    break
            else:
                display = f"{_format_magnitude(value_in_bytes)} bytes{rate_label}"
    elif quantity is not None and time_unit and not rate_time_unit:
        # Has time divisor but rate is "none" → default to /s display
        per_sec = quantity.to(1 / ureg.second).magnitude
        display = _format_number(per_sec, "/s")
    else:
        # Pure number
        if target_unit not in ("auto", "none"):
            pint_target = _BYTE_UNITS.get(target_unit.lower())
            if not pint_target:
                raise ValueError(f"Unknown target unit: {target_unit}")
            converted = ureg.Quantity(magnitude, 'byte').to(pint_target).magnitude
            display = f"{_format_magnitude(converted)} {target_unit}{rate_label}"
        else:
            display = _format_number(magnitude, rate_label)

    return {
        "expression": expression,
        "result_display": display,
        "raw_value": magnitude,
    }
