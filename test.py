#!/usr/bin/env python3
"""
Test script to demonstrate filename-based extraction
For filenames like: CIPLA_transcript_Aug_2018, LUPIN_transcript_Aug_2018
"""

import re
from pathlib import Path

def test_filename_extraction():
    """Test the filename extraction logic"""
    
    # Test filenames
    test_files = [
        "CIPLA_transcript_Aug_2018.pdf",
        "LUPIN_transcript_Aug_2018.pdf", 
        "CIPLA_transcript_Jul_2020.pdf",
        "LUPIN_transcript_Dec_2019.pdf",
        "CIPLA_transcript_Mar_2021.pdf",
        "LUPIN_transcript_Jun_2022.pdf",
        "CIPLA_transcript_April_2023.pdf",
        "LUPIN_transcript_January_2024.pdf"
    ]
    
    print("🧪 Testing Filename Extraction Logic")
    print("=" * 60)
    
    for filename in test_files:
        print(f"\n📄 Testing: {filename}")
        
        # Extract company
        company = extract_company_from_filename(filename)
        
        # Extract quarter from month
        quarter = extract_quarter_from_filename(filename)
        
        # Extract fiscal year
        fiscal_year = extract_fiscal_year_from_filename(filename)
        
        # Extract date
        date = extract_date_from_filename(filename)
        
        print(f"  🏢 Company: {company}")
        print(f"  📊 Quarter: {quarter}")
        print(f"  📅 Fiscal Year: {fiscal_year}")
        print(f"  📆 Date: {date}")
        
        # Show expected JSON structure
        expected_json = {
            "company": company,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "report_date": date,
            "filename": filename
        }
        
        print(f"  💾 JSON Preview: {expected_json}")

def extract_company_from_filename(filename):
    """Extract company from filename"""
    filename_upper = filename.upper()
    if 'CIPLA' in filename_upper:
        return "CIPLA"
    elif 'LUPIN' in filename_upper:
        return "LUPIN"
    return "UNKNOWN"

def extract_quarter_from_filename(filename):
    """Extract quarter based on month in filename"""
    month_to_quarter = {
        # Q1: April-June (Indian fiscal year)
        'apr': 'Q1', 'april': 'Q1', 'may': 'Q1', 'jun': 'Q1', 'june': 'Q1',
        # Q2: July-September  
        'jul': 'Q2', 'july': 'Q2', 'aug': 'Q2', 'august': 'Q2', 'sep': 'Q2', 'september': 'Q2',
        # Q3: October-December
        'oct': 'Q3', 'october': 'Q3', 'nov': 'Q3', 'november': 'Q3', 'dec': 'Q3', 'december': 'Q3',
        # Q4: January-March
        'jan': 'Q4', 'january': 'Q4', 'feb': 'Q4', 'february': 'Q4', 'mar': 'Q4', 'march': 'Q4'
    }
    
    filename_lower = filename.lower()
    
    # Look for month in filename
    for month, quarter in month_to_quarter.items():
        if month in filename_lower:
            return quarter
    
    return "Unknown Quarter"

def extract_fiscal_year_from_filename(filename):
    """Extract fiscal year from filename"""
    # Look for 4-digit year
    year_pattern = r'(\d{4})'
    matches = re.findall(year_pattern, filename)
    
    if matches:
        calendar_year = int(matches[-1])  # Take the last year found
        
        # Determine fiscal year based on month
        month_match = re.search(r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)', filename.lower())
        
        if month_match:
            month = month_match.group(1)
            
            # Indian fiscal year logic: April to March
            if month in ['jan', 'january', 'feb', 'february', 'mar', 'march']:
                fiscal_year = calendar_year  # Jan-Mar belongs to same FY
            else:
                fiscal_year = calendar_year + 1  # Apr-Dec belongs to next FY
            
            return str(fiscal_year)
        
        return str(calendar_year)
    
    return "Unknown Year"

def extract_date_from_filename(filename):
    """Extract or construct date from filename"""
    month_names = {
        'jan': 'January', 'january': 'January',
        'feb': 'February', 'february': 'February', 
        'mar': 'March', 'march': 'March',
        'apr': 'April', 'april': 'April',
        'may': 'May',
        'jun': 'June', 'june': 'June',
        'jul': 'July', 'july': 'July',
        'aug': 'August', 'august': 'August',
        'sep': 'September', 'september': 'September',
        'oct': 'October', 'october': 'October',
        'nov': 'November', 'november': 'November',
        'dec': 'December', 'december': 'December'
    }
    
    # Extract month and year
    month_year_pattern = r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)_(\d{4})'
    
    filename_lower = filename.lower()
    match = re.search(month_year_pattern, filename_lower)
    
    if match:
        month_abbr = match.group(1)
        year = match.group(2)
        month_full = month_names.get(month_abbr, month_abbr.title())
        
        # Construct date (default to mid-month for earnings calls)
        return f"{month_full} 15, {year}"
    
    return "Unknown Date"

def show_quarter_mapping():
    """Show the quarter mapping logic"""
    print("\n📊 Quarter Mapping Logic (Indian Fiscal Year):")
    print("-" * 50)
    print("Q1 (Apr-Jun): April, May, June")
    print("Q2 (Jul-Sep): July, August, September") 
    print("Q3 (Oct-Dec): October, November, December")
    print("Q4 (Jan-Mar): January, February, March")
    print("\n📅 Fiscal Year Logic:")
    print("- Jan-Mar 2018 → FY 2018")
    print("- Apr-Dec 2018 → FY 2019")

if __name__ == "__main__":
    test_filename_extraction()
    show_quarter_mapping()