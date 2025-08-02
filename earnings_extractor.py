import fitz  # PyMuPDF
import json
import re
from datetime import datetime
from pathlib import Path

class EarningsCallExtractor:
    def __init__(self):
        self.company_patterns = {
            'lupin': r'LUPIN|Lupin Limited',
            'cipla': r'CIPLA|Cipla Limited'
        }
        
    def extract_from_pdf(self, pdf_path):
        """Main extraction function"""
        print(f"🔄 Processing: {Path(pdf_path).name}")
        
        # Extract raw text
        raw_text = self._extract_text_from_pdf(pdf_path)
        
        # Get filename for pattern matching
        filename = Path(pdf_path).name
        
        # Extract structured data
        data = {
            "company": self._extract_company_name(raw_text, filename),
            "report_date": self._extract_report_date(raw_text, filename),
            "filename": filename,
            "quarter": self._extract_quarter_info(raw_text, filename),
            "fiscal_year": self._extract_fiscal_year(raw_text, filename),
            "management_team": self._extract_management_team(raw_text),
            "moderator": self._extract_moderator(raw_text),
            "analysts": self._extract_analysts(raw_text),
            "qa_segments": self._extract_qa_segments(raw_text),
            "key_financial_metrics": self._extract_financial_metrics(raw_text),
            "business_highlights": self._extract_business_highlights(raw_text),
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "source_file": pdf_path,
                "text_length": len(raw_text),
                "extraction_method": "PyMuPDF + Regex parsing + Filename analysis"
            }
        }
        
        # Print extraction summary
        print(f"  📊 Extracted: {data['company']} {data['quarter']} FY{data['fiscal_year']}")
        
        return data
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract raw text from PDF"""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text += f"\n--- PAGE {page_num + 1} ---\n"
                full_text += text
            
            doc.close()
            return full_text
            
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return ""
    
    def _extract_company_name(self, text, filename):
        """Extract company name"""
        # Try from filename first
        filename_upper = filename.upper()
        if 'LUPIN' in filename_upper:
            return "LUPIN"
        elif 'CIPLA' in filename_upper:
            return "CIPLA"
        
        # Try from text content
        for company, pattern in self.company_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return company.upper()
        
        return "UNKNOWN"
    
    def _extract_report_date(self, text, filename=""):
        """Extract the report/call date from text or filename"""
        # First try to extract from text content
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # If not found in text, try to construct from filename
        return self._extract_date_from_filename(filename)
    
    def _extract_date_from_filename(self, filename):
        """Extract or construct date from filename"""
        # Patterns like "Aug_2018", "August_2018"
        month_year_patterns = [
            r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)_(\d{4})',
            r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)(\d{4})'
        ]
        
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
        
        filename_lower = filename.lower()
        
        for pattern in month_year_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                month_abbr = match.group(1)
                year = match.group(2)
                month_full = month_names.get(month_abbr, month_abbr.title())
                
                # Default to mid-month for earnings calls
                constructed_date = f"{month_full} 15, {year}"
                print(f"  📅 Constructed date from filename: {constructed_date}")
                return constructed_date
        
        return "Unknown Date"
    
    def _extract_quarter_info(self, text, filename=""):
        """Extract quarter information from text or filename"""
        # First try to extract from text content
        quarter_patterns = [
            r'Q(\d+)\s+FY',
            r'Quarter\s*(\d+)',
            r'Q(\d+)\s+\d{4}',
            r'(\d+)(?:st|nd|rd|th)?\s+quarter'
        ]
        
        for pattern in quarter_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"Q{match.group(1)}"
        
        # If not found in text, try to determine from filename month
        return self._determine_quarter_from_filename(filename)
    
    def _determine_quarter_from_filename(self, filename):
        """Determine quarter from month in filename"""
        month_to_quarter = {
            # Q1: April-June
            'apr': 'Q1', 'april': 'Q1', 'may': 'Q1', 'jun': 'Q1', 'june': 'Q1',
            # Q2: July-September  
            'jul': 'Q2', 'july': 'Q2', 'aug': 'Q2', 'august': 'Q2', 'sep': 'Q2', 'september': 'Q2',
            # Q3: October-December
            'oct': 'Q3', 'october': 'Q3', 'nov': 'Q3', 'november': 'Q3', 'dec': 'Q3', 'december': 'Q3',
            # Q4: January-March
            'jan': 'Q4', 'january': 'Q4', 'feb': 'Q4', 'february': 'Q4', 'mar': 'Q4', 'march': 'Q4'
        }
        
        # Extract month from filename patterns like "Aug_2018", "August_2018", etc.
        month_patterns = [
            r'_(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)_',
            r'_(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\d{4}',
            r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)_\d{4}'
        ]
        
        filename_lower = filename.lower()
        
        for pattern in month_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                month = match.group(1)
                quarter = month_to_quarter.get(month, 'Unknown Quarter')
                print(f"  📅 Detected month '{month}' from filename → {quarter}")
                return quarter
        
        # Try to find month anywhere in filename
        for month, quarter in month_to_quarter.items():
            if month in filename_lower:
                print(f"  📅 Found month '{month}' in filename → {quarter}")
                return quarter
        
        return "Unknown Quarter"
    
    def _extract_fiscal_year(self, text, filename=""):
        """Extract fiscal year from text or filename"""
        # First try to extract from text content
        fy_patterns = [
            r'FY\s*[\'"]?(\d{2,4})',
            r'FY(\d{2,4})',
            r'Financial Year\s+(\d{4})',
            r'fiscal\s+year\s+(\d{4})',
            r'fiscal\s+(\d{4})'
        ]
        
        for pattern in fy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                # Convert 2-digit to 4-digit year if needed
                if len(year) == 2:
                    year = "20" + year
                return year
        
        # If not found in text, extract from filename
        return self._extract_year_from_filename(filename)
    
    def _extract_year_from_filename(self, filename):
        """Extract year from filename patterns"""
        # Look for 4-digit year in filename
        year_pattern = r'(\d{4})'
        matches = re.findall(year_pattern, filename)
        
        if matches:
            year = matches[-1]  # Take the last year found
            
            # Determine fiscal year based on month and year
            month_match = re.search(r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)', filename.lower())
            
            if month_match:
                month = month_match.group(1)
                calendar_year = int(year)
                
                # Indian fiscal year logic: April to March
                # Q1 FY19 = Apr-Jun 2018, Q2 FY19 = Jul-Sep 2018, etc.
                if month in ['jan', 'january', 'feb', 'february', 'mar', 'march']:
                    fiscal_year = calendar_year  # Jan-Mar belongs to same FY
                else:
                    fiscal_year = calendar_year + 1  # Apr-Dec belongs to next FY
                
                print(f"  📅 Calendar year: {calendar_year}, Month: {month} → Fiscal Year: {fiscal_year}")
                return str(fiscal_year)
            
            return year
        
        return "Unknown Year"
    
    def _extract_management_team(self, text):
        """Extract management team members"""
        management = []
        
        # Pattern for management section
        mgmt_patterns = [
            r'MANAGEMENT:\s*(.*?)(?=MODERATOR:|Moderator:|\n\n)',
            r'From.*?management.*?we have.*?(.*?)(?=\n\n|Moderator)',
        ]
        
        for pattern in mgmt_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                mgmt_text = match.group(1)
                
                # Extract individual members
                member_patterns = [
                    r'(MR\.|MS\.|DR\.)\s+([A-Z\s]+?)\s*[–-]\s*([^–\n]+)',
                    r'([A-Z]+\s+[A-Z]+)\s*[–-]\s*([^–\n]+)',
                ]
                
                for member_pattern in member_patterns:
                    matches = re.findall(member_pattern, mgmt_text)
                    for match in matches:
                        if len(match) == 3:  # Title, Name, Position
                            title, name, position = match
                            member_info = f"{title.strip()} {name.strip()} - {position.strip()}"
                        else:  # Name, Position
                            name, position = match
                            member_info = f"{name.strip()} - {position.strip()}"
                        
                        if member_info not in management:
                            management.append(member_info)
        
        return management if management else ["Management information not found"]
    
    def _extract_moderator(self, text):
        """Extract moderator information"""
        moderator_patterns = [
            r'MODERATOR:\s*([^\.]+)',
            r'Moderator:\s*([^\n]+)',
        ]
        
        for pattern in moderator_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Moderator information not found"
    
    def _extract_analysts(self, text):
        """Extract analyst information from Q&A section"""
        analysts = []
        
        # Pattern for analyst introductions
        analyst_pattern = r'(?:question|Next question).*?from.*?line of ([^.]+) (?:from|with) ([^.]+)\.'
        
        matches = re.findall(analyst_pattern, text, re.IGNORECASE)
        
        seen_analysts = set()
        for analyst_name, firm in matches:
            analyst_name = analyst_name.strip()
            firm = firm.strip()
            
            if analyst_name not in seen_analysts:
                analysts.append({
                    "name": analyst_name,
                    "firm": firm
                })
                seen_analysts.add(analyst_name)
        
        return analysts
    
    def _extract_qa_segments(self, text):
        """Extract Q&A segments"""
        qa_segments = []
        
        # Find Q&A section
        qa_start_patterns = [
            r'question.*?answer.*?session',
            r'open.*?floor.*?discussion',
            r'first question'
        ]
        
        qa_start = -1
        for pattern in qa_start_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                qa_start = match.start()
                break
        
        if qa_start == -1:
            return qa_segments
        
        qa_text = text[qa_start:]
        
        # Split by question introductions
        question_splits = re.split(
            r'(?:Next question|The question|question).*?comes from.*?line of ([^.]+) (?:from|with) ([^.]+)\.',
            qa_text,
            flags=re.IGNORECASE
        )
        
        for i in range(1, len(question_splits), 3):
            if i + 2 >= len(question_splits):
                break
                
            analyst = question_splits[i].strip()
            firm = question_splits[i + 1].strip()
            qa_content = question_splits[i + 2].strip()
            
            # Parse questions and answers from the content
            qa_pair = self._parse_qa_content(qa_content)
            
            if qa_pair['question']:
                qa_segments.append({
                    "analyst_name": analyst,
                    "analyst_firm": firm,
                    "question": qa_pair['question'],
                    "answers": qa_pair['answers']
                })
        
        return qa_segments
    
    def _parse_qa_content(self, content):
        """Parse question and answer from content"""
        qa_pair = {
            "question": "",
            "answers": []
        }
        
        # Split by speaker names
        speaker_pattern = r'([A-Za-z\s]+):'
        parts = re.split(speaker_pattern, content)
        
        current_speaker = None
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            
            # Check if this is a speaker name
            if re.match(r'^[A-Za-z\s]+$', part) and i + 1 < len(parts):
                current_speaker = part
            elif current_speaker:
                # This is content from the current speaker
                if not qa_pair['question'] and any(name in current_speaker.lower() for name in ['analyst', 'question']):
                    qa_pair['question'] = part[:500]  # Limit length
                elif current_speaker in ['Umang Vohra', 'Kedar Upadhye', 'Vinita Gupta', 'Ramesh Swaminathan', 'Nilesh Gupta']:
                    qa_pair['answers'].append({
                        "speaker": current_speaker,
                        "response": part[:500]  # Limit length
                    })
        
        return qa_pair
    
    def _extract_financial_metrics(self, text):
        """Extract financial metrics"""
        metrics = {}
        
        # Revenue patterns
        revenue_patterns = [
            (r'revenue.*?(?:of|at|was)\s*(?:INR|Rs\.?)\s*([0-9,]+)\s*crores?', 'revenue_inr_crores'),
            (r'revenue.*?(?:of|at|was)\s*\$\s*([0-9,]+)\s*million', 'revenue_usd_million'),
            (r'sales.*?(?:of|at|was)\s*(?:INR|Rs\.?)\s*([0-9,]+)\s*crores?', 'sales_inr_crores'),
        ]
        
        # Growth patterns
        growth_patterns = [
            (r'growth.*?(?:of|at|was)\s*([0-9]+\.?[0-9]*)\s*%', 'growth_percentage'),
            (r'increased.*?(?:by|to)\s*([0-9]+\.?[0-9]*)\s*%', 'increase_percentage'),
        ]
        
        # EBITDA patterns
        ebitda_patterns = [
            (r'EBITDA.*?(?:of|at|was)\s*([0-9]+\.?[0-9]*)\s*%', 'ebitda_margin_percentage'),
            (r'EBITDA.*?(?:of|at|was)\s*(?:INR|Rs\.?)\s*([0-9,]+)\s*crores?', 'ebitda_inr_crores'),
        ]
        
        all_patterns = revenue_patterns + growth_patterns + ebitda_patterns
        
        for pattern, metric_name in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the first match and clean it
                value = matches[0].replace(',', '')
                metrics[metric_name] = value
        
        return metrics
    
    def _extract_business_highlights(self, text):
        """Extract business highlights and key points"""
        highlights = []
        
        # Look for key business terms and context
        highlight_patterns = [
            r'(launched.*?(?:product|brand|initiative)[^.]*\.)',
            r'(approved.*?(?:by|from).*?(?:FDA|authority)[^.]*\.)',
            r'(partnership.*?with.*?[^.]*\.)',
            r'(acquired.*?[^.]*\.)',
            r'(expanded.*?(?:presence|operations)[^.]*\.)',
        ]
        
        for pattern in highlight_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 20:  # Filter out very short matches
                    highlights.append(match.strip())
        
        # Limit to top 10 highlights
        return highlights[:10]
    
    def save_to_json(self, data, output_path):
        """Save extracted data to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Data saved to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False

# Main function for testing
def main():
    extractor = EarningsCallExtractor()
    
    # Test with sample PDF (you'll replace this with your actual PDF path)
    pdf_path = "data/sample.pdf"  # Replace with your PDF path
    
    if Path(pdf_path).exists():
        data = extractor.extract_from_pdf(pdf_path)
        
        # Save to output folder
        output_file = f"output/{data['company']}_{data['quarter']}_{data['fiscal_year']}_extracted.json"
        extractor.save_to_json(data, output_file)
        
        # Print summary
        print("\n📋 Extraction Summary:")
        print(f"Company: {data['company']}")
        print(f"Quarter: {data['quarter']} {data['fiscal_year']}")
        print(f"Management Team: {len(data['management_team'])} members")
        print(f"Analysts: {len(data['analysts'])} analysts")
        print(f"Q&A Segments: {len(data['qa_segments'])} segments")
        print(f"Financial Metrics: {len(data['key_financial_metrics'])} metrics")
        
    else:
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please add your PDF files to the data/ folder")

if __name__ == "__main__":
    main()