# -*- coding: utf-8 -*-
"""
Ethiopian Calendar Conversion Utility

This module provides functions to convert between Gregorian and Ethiopian calendars.
The Ethiopian calendar has 13 months - 12 months of 30 days each and a 13th month (Pagume) 
of 5 or 6 days depending on whether it's a leap year.
"""

from datetime import date, timedelta

# Amharic month names
AMHARIC_MONTHS = [
    'መስከረም', 'ጥቅምት', 'ኅዳር', 'ታኅሣሥ',
    'ጥር', 'የካቲት', 'መጋቢት', 'ሚያዝያ',
    'ግንቦት', 'ሰኔ', 'ሐምሌ', 'ነሐሴ', 'ጳጉሜን'
]


def is_ethiopian_leap_year(year):
    """
    Check if an Ethiopian year is a leap year.
    
    :param year: Ethiopian year
    :return: True if leap year, False otherwise
    """
    return (year % 4) == 3


def gregorian_to_ethiopian(greg_date):
    """
    Convert a Gregorian date to Ethiopian calendar.
    
    :param greg_date: datetime.date object or date string
    :return: tuple (ethiopian_year, ethiopian_month, ethiopian_day)
    """
    if not greg_date:
        return None, None, None
    
    if isinstance(greg_date, str):
        greg_date = date.fromisoformat(greg_date)
    
    # Ethiopian calendar epoch: September 11, 8 CE (Gregorian)
    # or September 12 in Gregorian leap years
    
    # Calculate the difference from the Ethiopian epoch
    ethiopian_epoch = date(8, 9, 11)
    
    # Adjust for leap years
    if greg_date.year % 4 == 0 and (greg_date.year % 100 != 0 or greg_date.year % 400 == 0):
        if greg_date.month < 9 or (greg_date.month == 9 and greg_date.day < 12):
            ethiopian_epoch = date(8, 9, 12)
    
    # Calculate days since epoch
    days_since_epoch = (greg_date - ethiopian_epoch).days
    
    # Ethiopian year starts on September 11 (or 12 in leap years)
    # Calculate the Ethiopian year
    eth_year = greg_date.year - 8
    
    # Determine the start of the current Ethiopian year in Gregorian calendar
    if greg_date.year % 4 == 0 and (greg_date.year % 100 != 0 or greg_date.year % 400 == 0):
        eth_new_year = date(greg_date.year, 9, 12)
    else:
        eth_new_year = date(greg_date.year, 9, 11)
    
    # If we're before the Ethiopian new year, we're still in the previous Ethiopian year
    if greg_date < eth_new_year:
        eth_year -= 1
        # Recalculate the start of the Ethiopian year
        prev_year = greg_date.year - 1
        if prev_year % 4 == 0 and (prev_year % 100 != 0 or prev_year % 400 == 0):
            eth_new_year = date(prev_year, 9, 12)
        else:
            eth_new_year = date(prev_year, 9, 11)
    
    # Calculate days since the start of the Ethiopian year
    days_in_year = (greg_date - eth_new_year).days + 1
    
    # Calculate Ethiopian month and day
    if days_in_year <= 360:
        eth_month = ((days_in_year - 1) // 30) + 1
        eth_day = ((days_in_year - 1) % 30) + 1
    else:
        # 13th month (Pagume)
        eth_month = 13
        eth_day = days_in_year - 360
    
    return eth_year, eth_month, eth_day


def format_ethiopian_date(greg_date):
    """
    Format a Gregorian date as an Ethiopian date string with Amharic month names.
    
    :param greg_date: datetime.date object or date string
    :return: Formatted Ethiopian date string (e.g., "15 መስከረም 2016")
    """
    if not greg_date:
        return ""
    
    eth_year, eth_month, eth_day = gregorian_to_ethiopian(greg_date)
    
    if eth_year is None:
        return ""
    
    month_name = AMHARIC_MONTHS[eth_month - 1]
    return f"{eth_day} {month_name} {eth_year}"


def ethiopian_to_gregorian(eth_year, eth_month, eth_day):
    """
    Convert an Ethiopian date to Gregorian calendar.
    
    :param eth_year: Ethiopian year
    :param eth_month: Ethiopian month (1-13)
    :param eth_day: Ethiopian day
    :return: datetime.date object
    """
    # Calculate the Gregorian year
    greg_year = eth_year + 8
    
    # Determine the start of the Ethiopian year in Gregorian calendar
    if greg_year % 4 == 0 and (greg_year % 100 != 0 or greg_year % 400 == 0):
        eth_new_year = date(greg_year, 9, 12)
    else:
        eth_new_year = date(greg_year, 9, 11)
    
    # Calculate days to add
    if eth_month <= 12:
        days_to_add = (eth_month - 1) * 30 + (eth_day - 1)
    else:
        # 13th month
        days_to_add = 360 + (eth_day - 1)
    
    # Calculate the Gregorian date
    greg_date = eth_new_year + timedelta(days=days_to_add)
    
    return greg_date
