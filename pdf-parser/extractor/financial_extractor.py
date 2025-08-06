# pdf-parser/extractor/financial_extractor.py

import re
from typing import Dict, List, Any

class FinancialExtractor:
    """Extract financial metrics using regex patterns"""
    
    @staticmethod
    def extract_all_metrics(text: str) -> Dict[str, Any]:
        """Extract all financial metrics from text"""
        return {
            "revenue": FinancialExtractor.extract_revenue(text),
            "growth_rates": FinancialExtractor.extract_growth_rates(text),
            "ebitda": FinancialExtractor.extract_ebitda(text),
            "margins": FinancialExtractor.extract_margins(text),
            "quarter_info": FinancialExtractor.extract_quarter_info(text)
        }
    
    @staticmethod
    def extract_revenue(text: str) -> List[Dict[str, Any]]:
        """Extract revenue patterns"""
        revenue_patterns = [
            r'(?:revenue|income|sales|turnover)\s+(?:of\s+)?(?:Rs\.?|INR)\s*([\d,]+\.?\d*)\s*(?:crores?|cr)',
            r'(?:revenue|income|sales|turnover)\s+(?:of\s+)?(?:\$|USD)\s*([\d,]+\.?\d*)\s*(?:million|mn|billion|bn)',
            r'(?:Rs\.?|INR)\s*([\d,]+\.?\d*)\s*(?:crores?|cr)\s+(?:in\s+)?(?:revenue|income|sales|turnover)',
            r'(?:\$|USD)\s*([\d,]+\.?\d*)\s*(?:million|mn|billion|bn)\s+(?:in\s+)?(?:revenue|income|sales|turnover)',
            r'(?:total\s+)?(?:revenue|income|sales|turnover)[\s\w]*(?:Rs\.?|INR)\s*([\d,]+\.?\d*)\s*(?:crores?|cr)',
        ]
        
        results = []
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                raw_text = match.group(0)
                value = match.group(1).replace(',', '')
                
                # Determine currency and unit
                currency = "INR" if "Rs" in raw_text or "INR" in raw_text else "USD"
                unit = "crores" if "crore" in raw_text.lower() or "cr" in raw_text.lower() else (
                    "million" if "million" in raw_text.lower() or "mn" in raw_text.lower() else "billion"
                )
                
                results.append({
                    "raw_text": raw_text,
                    "value": float(value) if '.' in value else int(value),
                    "currency": currency,
                    "unit": unit
                })
        
        return results
    
    @staticmethod
    def extract_growth_rates(text: str) -> List[Dict[str, Any]]:
        """Extract growth rate patterns"""
        growth_patterns = [
            r'([\d]+\.?\d*)\s*%\s+(?:growth|increase|rise)',
            r'(?:grew|increased|rose)\s+(?:by\s+)?([\d]+\.?\d*)\s*%',
            r'(?:growth|increase|rise)\s+(?:of\s+)?([\d]+\.?\d*)\s*%',
            r'(?:year-on-year|YoY|y-o-y)\s+(?:growth\s+)?(?:of\s+)?([\d]+\.?\d*)\s*%',
            r'(?:quarter-on-quarter|QoQ|q-o-q)\s+(?:growth\s+)?(?:of\s+)?([\d]+\.?\d*)\s*%',
            r'(?:up|down)\s+([\d]+\.?\d*)\s*%',
        ]
        
        results = []
        for pattern in growth_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                raw_text = match.group(0)
                value = match.group(1)
                
                # Determine type
                growth_type = "YoY" if any(x in raw_text.lower() for x in ['year-on-year', 'yoy', 'y-o-y']) else (
                    "QoQ" if any(x in raw_text.lower() for x in ['quarter-on-quarter', 'qoq', 'q-o-q']) else "general"
                )
                
                # Determine direction
                direction = "negative" if "down" in raw_text.lower() else "positive"
                
                results.append({
                    "raw_text": raw_text,
                    "value": float(value),
                    "type": growth_type,
                    "direction": direction
                })
        
        return results
    
    @staticmethod
    def extract_ebitda(text: str) -> List[Dict[str, Any]]:
        """Extract EBITDA patterns"""
        ebitda_patterns = [
            r'EBITDA\s+(?:of\s+)?(?:Rs\.?|INR)\s*([\d,]+\.?\d*)\s*(?:crores?|cr)',
            r'EBITDA\s+(?:of\s+)?(?:\$|USD)\s*([\d,]+\.?\d*)\s*(?:million|mn|billion|bn)',
            r'EBITDA\s+(?:stands?\s+at|is|was)\s+(?:Rs\.?|INR)\s*([\d,]+\.?\d*)\s*(?:crores?|cr)',
            r'(?:Rs\.?|INR)\s*([\d,]+\.?\d*)\s*(?:crores?|cr)\s+(?:in\s+)?EBITDA',
        ]
        
        results = []
        for pattern in ebitda_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                raw_text = match.group(0)
                value = match.group(1).replace(',', '')
                
                currency = "INR" if "Rs" in raw_text or "INR" in raw_text else "USD"
                unit = "crores" if "crore" in raw_text.lower() or "cr" in raw_text.lower() else (
                    "million" if "million" in raw_text.lower() or "mn" in raw_text.lower() else "billion"
                )
                
                results.append({
                    "raw_text": raw_text,
                    "value": float(value) if '.' in value else int(value),
                    "currency": currency,
                    "unit": unit
                })
        
        return results
    
    @staticmethod
    def extract_margins(text: str) -> List[Dict[str, Any]]:
        """Extract margin patterns"""
        margin_patterns = [
            r'([\d]+\.?\d*)\s*%\s+(?:EBITDA\s+)?margin',
            r'(?:EBITDA\s+)?margin\s+(?:of\s+)?([\d]+\.?\d*)\s*%',
            r'([\d]+\.?\d*)\s*%\s+to\s+sales',
            r'(?:gross|operating|net|profit)\s+margin\s+(?:of\s+)?([\d]+\.?\d*)\s*%',
            r'margin\s+(?:stands?\s+at|is|was)\s+([\d]+\.?\d*)\s*%',
        ]
        
        results = []
        for pattern in margin_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                raw_text = match.group(0)
                value = match.group(1)
                
                # Determine margin type
                margin_type = "EBITDA" if "ebitda" in raw_text.lower() else (
                    "gross" if "gross" in raw_text.lower() else (
                        "operating" if "operating" in raw_text.lower() else (
                            "net" if "net" in raw_text.lower() else "general"
                        )
                    )
                )
                
                results.append({
                    "raw_text": raw_text,
                    "value": float(value),
                    "type": margin_type
                })
        
        return results
    
    @staticmethod
    def extract_quarter_info(text: str) -> Dict[str, List[str]]:
        """Extract quarterly and fiscal year references"""
        quarter_info = {
            "quarters": [],
            "fiscal_years": [],
            "combined": []
        }
        
        # Extract quarters
        quarter_pattern = r'\b(Q[1-4])\b'
        quarters = re.findall(quarter_pattern, text, re.IGNORECASE)
        quarter_info["quarters"] = list(set(quarters))
        
        # Extract fiscal years
        fy_patterns = [
            r'\bFY\s*(\d{2,4})\b',
            r'\bFY(\d{2,4})\b',
            r'\b(?:fiscal\s+year\s+)?(\d{4})-(\d{2,4})\b'
        ]
        
        fiscal_years = set()
        for pattern in fy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:  # For patterns like 2018-19
                    fiscal_years.add(f"FY{match.group(2)}")
                else:
                    year = match.group(1)
                    if len(year) == 2:
                        fiscal_years.add(f"FY{year}")
                    else:
                        fiscal_years.add(f"FY{year[-2:]}")
        
        quarter_info["fiscal_years"] = sorted(list(fiscal_years))
        
        # Extract combined quarter+FY references
        combined_pattern = r'\b(Q[1-4])\s*FY\s*(\d{2,4})\b'
        combined_matches = re.finditer(combined_pattern, text, re.IGNORECASE)
        for match in combined_matches:
            quarter = match.group(1).upper()
            year = match.group(2)
            if len(year) == 2:
                quarter_info["combined"].append(f"{quarter} FY{year}")
            else:
                quarter_info["combined"].append(f"{quarter} FY{year[-2:]}")
        
        quarter_info["combined"] = list(set(quarter_info["combined"]))
        
        return quarter_info