"""
Timezone Engine for Quiet Hours Enforcement

Determines contact timezone and enforces quiet hours (9 PM - 8 AM local).
Uses area code mapping for US phone numbers with fallback chain.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz
import logging

logger = logging.getLogger(__name__)

# Area code to timezone mapping (US)
# Comprehensive mapping of major US area codes to their timezones
AREA_CODE_TIMEZONES = {
    # Eastern Time
    '201': 'America/New_York', '202': 'America/New_York', '203': 'America/New_York',
    '212': 'America/New_York', '215': 'America/New_York', '216': 'America/New_York',
    '301': 'America/New_York', '302': 'America/New_York', '305': 'America/New_York',
    '313': 'America/New_York', '404': 'America/New_York', '407': 'America/New_York',
    '410': 'America/New_York', '412': 'America/New_York', '470': 'America/New_York',
    '513': 'America/New_York', '516': 'America/New_York', '517': 'America/New_York',
    '603': 'America/New_York', '607': 'America/New_York', '617': 'America/New_York',
    '703': 'America/New_York', '704': 'America/New_York', '718': 'America/New_York',
    '727': 'America/New_York', '732': 'America/New_York', '757': 'America/New_York',
    '786': 'America/New_York', '802': 'America/New_York', '803': 'America/New_York',
    '804': 'America/New_York', '810': 'America/New_York', '813': 'America/New_York',
    '814': 'America/New_York', '828': 'America/New_York', '845': 'America/New_York',
    '850': 'America/New_York', '856': 'America/New_York', '860': 'America/New_York',
    '862': 'America/New_York', '863': 'America/New_York', '864': 'America/New_York',
    '865': 'America/New_York', '904': 'America/New_York', '908': 'America/New_York',
    '910': 'America/New_York', '912': 'America/New_York', '914': 'America/New_York',
    '917': 'America/New_York', '919': 'America/New_York', '929': 'America/New_York',
    '941': 'America/New_York', '973': 'America/New_York', '978': 'America/New_York',
    '980': 'America/New_York',

    # Central Time
    '205': 'America/Chicago', '214': 'America/Chicago', '217': 'America/Chicago',
    '251': 'America/Chicago', '256': 'America/Chicago', '281': 'America/Chicago',
    '309': 'America/Chicago', '312': 'America/Chicago', '314': 'America/Chicago',
    '316': 'America/Chicago', '318': 'America/Chicago', '319': 'America/Chicago',
    '331': 'America/Chicago', '334': 'America/Chicago', '337': 'America/Chicago',
    '361': 'America/Chicago', '409': 'America/Chicago', '414': 'America/Chicago',
    '417': 'America/Chicago', '430': 'America/Chicago', '432': 'America/Chicago',
    '469': 'America/Chicago', '479': 'America/Chicago', '501': 'America/Chicago',
    '504': 'America/Chicago', '507': 'America/Chicago', '512': 'America/Chicago',
    '515': 'America/Chicago', '563': 'America/Chicago', '573': 'America/Chicago',
    '601': 'America/Chicago', '608': 'America/Chicago', '612': 'America/Chicago',
    '618': 'America/Chicago', '620': 'America/Chicago', '630': 'America/Chicago',
    '636': 'America/Chicago', '641': 'America/Chicago', '651': 'America/Chicago',
    '660': 'America/Chicago', '662': 'America/Chicago', '682': 'America/Chicago',
    '708': 'America/Chicago', '712': 'America/Chicago', '713': 'America/Chicago',
    '715': 'America/Chicago', '773': 'America/Chicago', '785': 'America/Chicago',
    '806': 'America/Chicago', '815': 'America/Chicago', '816': 'America/Chicago',
    '817': 'America/Chicago', '830': 'America/Chicago', '832': 'America/Chicago',
    '847': 'America/Chicago', '870': 'America/Chicago', '901': 'America/Chicago',
    '903': 'America/Chicago', '913': 'America/Chicago', '918': 'America/Chicago',
    '920': 'America/Chicago', '936': 'America/Chicago', '940': 'America/Chicago',
    '956': 'America/Chicago', '972': 'America/Chicago', '979': 'America/Chicago',

    # Mountain Time
    '303': 'America/Denver', '307': 'America/Denver', '385': 'America/Denver',
    '406': 'America/Denver', '505': 'America/Denver', '575': 'America/Denver',
    '602': 'America/Phoenix', '623': 'America/Phoenix', '480': 'America/Phoenix',
    '520': 'America/Phoenix', '928': 'America/Phoenix',
    '605': 'America/Denver', '701': 'America/Denver', '702': 'America/Los_Angeles',
    '720': 'America/Denver', '775': 'America/Los_Angeles', '801': 'America/Denver',
    '915': 'America/Denver', '970': 'America/Denver',

    # Pacific Time
    '206': 'America/Los_Angeles', '209': 'America/Los_Angeles', '213': 'America/Los_Angeles',
    '253': 'America/Los_Angeles', '310': 'America/Los_Angeles', '323': 'America/Los_Angeles',
    '360': 'America/Los_Angeles', '408': 'America/Los_Angeles', '415': 'America/Los_Angeles',
    '425': 'America/Los_Angeles', '442': 'America/Los_Angeles', '510': 'America/Los_Angeles',
    '530': 'America/Los_Angeles', '541': 'America/Los_Angeles', '559': 'America/Los_Angeles',
    '562': 'America/Los_Angeles', '619': 'America/Los_Angeles', '626': 'America/Los_Angeles',
    '650': 'America/Los_Angeles', '657': 'America/Los_Angeles', '661': 'America/Los_Angeles',
    '669': 'America/Los_Angeles', '707': 'America/Los_Angeles', '714': 'America/Los_Angeles',
    '760': 'America/Los_Angeles', '805': 'America/Los_Angeles', '818': 'America/Los_Angeles',
    '831': 'America/Los_Angeles', '858': 'America/Los_Angeles', '909': 'America/Los_Angeles',
    '916': 'America/Los_Angeles', '925': 'America/Los_Angeles', '949': 'America/Los_Angeles',
    '951': 'America/Los_Angeles',

    # Alaska
    '907': 'America/Anchorage',

    # Hawaii
    '808': 'Pacific/Honolulu',
}

DEFAULT_QUIET_START = 21  # 9 PM
DEFAULT_QUIET_END = 8     # 8 AM
DEFAULT_TIMEZONE = 'America/Chicago'


def get_timezone_from_area_code(phone: str) -> Optional[str]:
    """
    Get timezone from phone area code.

    Args:
        phone: Phone number (any format)

    Returns:
        Timezone string or None if not found

    Examples:
        >>> get_timezone_from_area_code("+12125551234")
        "America/New_York"
        >>> get_timezone_from_area_code("415-555-1234")
        "America/Los_Angeles"
    """
    # Extract digits only
    digits = ''.join(c for c in phone if c.isdigit())

    # Handle +1 prefix (North American format)
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]

    if len(digits) >= 10:
        area_code = digits[:3]
        tz = AREA_CODE_TIMEZONES.get(area_code)
        if tz:
            logger.debug(f"Area code {area_code} mapped to {tz}")
        return tz

    logger.debug(f"Could not extract area code from phone: {phone}")
    return None


def get_contact_timezone(
    contact_tz: Optional[str],
    phone: Optional[str],
    location_tz: Optional[str]
) -> Tuple[str, str]:
    """
    Determine contact's timezone with fallback chain.

    Priority:
    1. Contact's explicitly set timezone
    2. Inferred from phone area code
    3. Location's default timezone
    4. System default (America/Chicago)

    Args:
        contact_tz: Contact's timezone setting
        phone: Contact's phone number
        location_tz: Location's timezone setting

    Returns:
        Tuple of (timezone_string, source)

    Examples:
        >>> get_contact_timezone("America/New_York", None, None)
        ("America/New_York", "contact")
        >>> get_contact_timezone(None, "+12125551234", None)
        ("America/New_York", "area_code")
    """
    # 1. Contact's explicit timezone
    if contact_tz:
        logger.debug(f"Using contact timezone: {contact_tz}")
        return (contact_tz, "contact")

    # 2. Infer from phone
    if phone:
        tz = get_timezone_from_area_code(phone)
        if tz:
            logger.debug(f"Using area code inferred timezone: {tz}")
            return (tz, "area_code")

    # 3. Location default
    if location_tz:
        logger.debug(f"Using location timezone: {location_tz}")
        return (location_tz, "location")

    # 4. System default
    logger.debug(f"Using system default timezone: {DEFAULT_TIMEZONE}")
    return (DEFAULT_TIMEZONE, "default")


def is_quiet_hours(
    timezone_str: str,
    quiet_start: int = DEFAULT_QUIET_START,
    quiet_end: int = DEFAULT_QUIET_END
) -> bool:
    """
    Check if current time is within quiet hours for the given timezone.

    Args:
        timezone_str: Timezone string (e.g., 'America/New_York')
        quiet_start: Hour when quiet hours begin (default 21 = 9 PM)
        quiet_end: Hour when quiet hours end (default 8 = 8 AM)

    Returns:
        True if currently in quiet hours

    Examples:
        >>> # If it's 10 PM in New York
        >>> is_quiet_hours("America/New_York", 21, 8)
        True
        >>> # If it's 2 PM in New York
        >>> is_quiet_hours("America/New_York", 21, 8)
        False
    """
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone: {timezone_str}, using default")
        tz = pytz.timezone(DEFAULT_TIMEZONE)

    local_now = datetime.now(tz)
    current_hour = local_now.hour

    # Quiet hours span midnight: 9 PM (21) to 8 AM
    if quiet_start > quiet_end:
        # e.g., 21-8: quiet if hour >= 21 OR hour < 8
        is_quiet = current_hour >= quiet_start or current_hour < quiet_end
    else:
        # e.g., 22-6: quiet if hour >= 22 AND hour < 6
        is_quiet = quiet_start <= current_hour < quiet_end

    logger.debug(
        f"Quiet hours check: {timezone_str} local time {local_now.strftime('%H:%M')}, "
        f"current_hour={current_hour}, quiet_start={quiet_start}, quiet_end={quiet_end}, "
        f"is_quiet={is_quiet}"
    )

    return is_quiet


def get_next_send_time(
    timezone_str: str,
    quiet_end: int = DEFAULT_QUIET_END
) -> datetime:
    """
    Get the next valid send time after quiet hours end.

    Args:
        timezone_str: Contact's timezone
        quiet_end: Hour when quiet hours end (default 8 = 8 AM)

    Returns:
        datetime in UTC of next valid send time

    Examples:
        >>> # If it's 10 PM, returns 8 AM tomorrow in UTC
        >>> get_next_send_time("America/New_York", 8)
        datetime(2026, 1, 7, 13, 0, 0, tzinfo=<UTC>)
    """
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone: {timezone_str}, using default")
        tz = pytz.timezone(DEFAULT_TIMEZONE)

    local_now = datetime.now(tz)

    # If before quiet_end today, send at quiet_end today
    if local_now.hour < quiet_end:
        next_send_local = local_now.replace(
            hour=quiet_end, minute=0, second=0, microsecond=0
        )
    else:
        # Send at quiet_end tomorrow
        tomorrow = local_now + timedelta(days=1)
        next_send_local = tomorrow.replace(
            hour=quiet_end, minute=0, second=0, microsecond=0
        )

    # Convert to UTC
    next_send_utc = next_send_local.astimezone(pytz.UTC)

    logger.info(
        f"Next send time for {timezone_str}: {next_send_local.strftime('%Y-%m-%d %H:%M %Z')} "
        f"(UTC: {next_send_utc.strftime('%Y-%m-%d %H:%M')})"
    )

    return next_send_utc
