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
        
        # Enhanced management names for better identification
        self.management_names = {
            'cipla': [
                'Umang Vohra', 'Kedar Upadhye', 'Samina Vaziralli', 'Rajesh Pradhan',
                'Ashish Adukia', 'Nikhil Chopra', 'Jaideep Gogtay'
            ],
            'lupin': [
                'Nilesh Gupta', 'Ramesh Swaminathan', 'Vinita Gupta', 'Rajeev Sibal',
                'Fabrice Egros', 'Cyrus Karkaria', 'Dr. Kamal Sharma', 'Kamal Sharma',
                'Sunil Makharia', 'Naresh Gupta', 'Rajiv Pillai', 'Arvind Bothra'
            ]
        }
        
    def extract_from_pdf(self, pdf_path):
        """Main extraction function with intelligent format detection"""
        print(f"🔄 Processing: {Path(pdf_path).name}")
        
        # Extract raw text
        raw_text = self._extract_text_from_pdf(pdf_path)
        
        # Get filename for pattern matching
        filename = Path(pdf_path).name
        company = self._extract_company_name(raw_text, filename)
        
        # Detect PDF format type
        pdf_format = self._detect_pdf_format(raw_text, company)
        print(f"  🔍 Detected format: {pdf_format}")
        
        # Extract structured data based on format
        if pdf_format == "structured_transcript":
            data = self._extract_structured_format(raw_text, filename, company)
        else:
            data = self._extract_general_format(raw_text, filename, company)
        
        # Print extraction summary
        print(f"  📊 Extracted: {data['company']} {data['quarter']} FY{data['fiscal_year']}")
        
        return data
    
    def _detect_pdf_format(self, text, company):
        """Detect if this is a structured transcript or general format"""
        # Look for structured transcript indicators
        structured_indicators = [
            r'MANAGEMENT:\s*DR\.|MR\.|MS\.',  # Lupin format
            r'Conference Call.*?\d{4}',
            r'Moderator:.*Ladies and gentlemen',
            r'good day and welcome',
            r'Page \d+ of \d+'
        ]
        
        for pattern in structured_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return "structured_transcript"
        
        return "general_format"
    
    def _extract_structured_format(self, text, filename, company):
        """Extract from structured earnings call transcripts (like Lupin)"""
        return {
            "company": company,
            "report_date": self._extract_report_date(text, filename),
            "filename": filename,
            "quarter": self._extract_quarter_info(text, filename),
            "fiscal_year": self._extract_fiscal_year(text, filename),
            "management_team": self._extract_management_structured(text, company),
            "moderator": self._extract_moderator_structured(text),
            "analysts": self._extract_analysts_structured(text),
            "qa_segments": self._extract_qa_structured(text, company),
            "key_financial_metrics": self._extract_financial_metrics(text),
            "business_highlights": self._extract_business_highlights(text),
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "source_file": filename,
                "text_length": len(text),
                "extraction_method": "Structured Transcript Parser",
                "format_detected": "structured_transcript"
            }
        }
    
    def _extract_general_format(self, text, filename, company):
        """Extract from general format documents (like Cipla)"""
        return {
            "company": company,
            "report_date": self._extract_report_date(text, filename),
            "filename": filename,
            "quarter": self._extract_quarter_info(text, filename),
            "fiscal_year": self._extract_fiscal_year(text, filename),
            "management_team": self._extract_management_team(text, company),
            "moderator": self._extract_moderator(text),
            "analysts": self._extract_analysts(text),
            "qa_segments": self._extract_qa_segments_improved(text, company),
            "key_financial_metrics": self._extract_financial_metrics(text),
            "business_highlights": self._extract_business_highlights(text),
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "source_file": filename,
                "text_length": len(text),
                "extraction_method": "General Format Parser",
                "format_detected": "general_format"
            }
        }
    
    def _extract_management_structured(self, text, company):
        """Extract management team from structured format"""
        management = []
        
        # Look for MANAGEMENT section with specific format
        mgmt_section_pattern = r'MANAGEMENT:\s*(.*?)(?=Page|\n\s*\n|\Z)'
        mgmt_match = re.search(mgmt_section_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if mgmt_match:
            mgmt_text = mgmt_match.group(1)
            
            # Extract individual management members
            member_patterns = [
                r'(DR\.|MR\.|MS\.)\s+([A-Z\s]+?)\s*[–-]\s*([^–\n]+)',
                r'([A-Z][A-Z\s]+?)\s*[–-]\s*([^–\n]+)',
            ]
            
            for pattern in member_patterns:
                matches = re.findall(pattern, mgmt_text)
                for match in matches:
                    if len(match) == 3:
                        title, name, position = match
                        management.append(f"{title.strip()} {name.strip()} - {position.strip()}")
                    elif len(match) == 2:
                        name, position = match
                        management.append(f"{name.strip()} - {position.strip()}")
        
        # Clean up management names
        cleaned_management = []
        for member in management:
            # Remove extra spaces and clean up
            cleaned = re.sub(r'\s+', ' ', member).strip()
            if len(cleaned) > 5 and cleaned not in cleaned_management:
                cleaned_management.append(cleaned)
        
        return cleaned_management if cleaned_management else ["Management information not found"]
    
    def _extract_moderator_structured(self, text):
        """Extract moderator from structured format"""
        moderator_patterns = [
            r'Moderator:\s*([^.\n]+)',
            r'moderator.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in moderator_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Moderator information not found"
    
    def _extract_analysts_structured(self, text):
        """Extract analysts from structured Q&A format"""
        analysts = []
        seen_analysts = set()
        
        # Multiple patterns for analyst identification
        analyst_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+from\s+([A-Z][a-zA-Z\s&\.]+)\.?\s*Please go ahead',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+from\s+([A-Z][a-zA-Z\s&\.]+)',
            r'question.*?from.*?line of\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+from\s+([^.]+)',
            r'The.*?question.*?is from\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+from\s+([^.]+)',
        ]
        
        for pattern in analyst_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                analyst_name = match[0].strip()
                firm = match[1].strip()
                
                # Clean firm name
                firm = re.sub(r'\s+', ' ', firm.replace('\n', ' '))
                firm = re.sub(r'\.?\s*Please go ahead.*$', '', firm)
                
                if analyst_name not in seen_analysts and len(analyst_name) > 3:
                    analysts.append({
                        "name": analyst_name,
                        "firm": firm
                    })
                    seen_analysts.add(analyst_name)
        
        return analysts
    
    def _extract_qa_structured(self, text, company):
        """Extract Q&A from structured format"""
        qa_segments = []
        mgmt_names = self.management_names.get(company.lower(), [])
        
        # Find all Q&A exchanges
        # Split by analyst questions
        analyst_intro_pattern = r'(?:The.*?question.*?is from|Thank you.*?We will take.*?question from.*?line of)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+from\s+([^.]+)\.?\s*Please go ahead\.'
        
        # Split text into segments
        segments = re.split(analyst_intro_pattern, text, flags=re.IGNORECASE)
        
        # Process segments in groups of 3 (text, analyst_name, firm)
        for i in range(1, len(segments), 3):
            if i + 2 >= len(segments):
                break
            
            analyst_name = segments[i].strip()
            analyst_firm = segments[i + 1].strip().replace('\n', ' ')
            segment_content = segments[i + 2]
            
            # Parse the Q&A content from this segment
            qa_pair = self._parse_structured_qa_content(segment_content, mgmt_names, analyst_name)
            
            if qa_pair['question'] or qa_pair['answers']:
                qa_segments.append({
                    "analyst_name": analyst_name,
                    "analyst_firm": analyst_firm,
                    "question": qa_pair['question'],
                    "answers": qa_pair['answers']
                })
        
        return qa_segments
    
    def _parse_structured_qa_content(self, content, mgmt_names, analyst_name):
        """Parse structured Q&A content"""
        qa_pair = {
            "question": "",
            "answers": []
        }
        
        # Split by speaker names (Name:)
        speaker_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s*'
        parts = re.split(speaker_pattern, content)
        
        current_speaker = None
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            
            # Check if this is a speaker name
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', part) and i + 1 < len(parts):
                current_speaker = part
            elif current_speaker and i > 0:
                content_text = part[:1500]  # Limit length
                
                # Determine speaker type
                is_management = any(name.split()[-1] in current_speaker for name in mgmt_names)
                is_analyst = current_speaker == analyst_name or 'analyst' in current_speaker.lower()
                
                if not qa_pair['question'] and (is_analyst or current_speaker == analyst_name):
                    # This is the analyst question
                    qa_pair['question'] = content_text
                elif is_management:
                    # This is a management response
                    qa_pair['answers'].append({
                        "speaker": current_speaker,
                        "response": content_text,
                        "speaker_type": "Management"
                    })
                elif qa_pair['question'] and current_speaker == analyst_name:
                    # Follow-up question from analyst
                    qa_pair['answers'].append({
                        "speaker": current_speaker,
                        "response": content_text,
                        "speaker_type": "Analyst Follow-up"
                    })
        
        return qa_pair
    
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
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'August \d{2}, \d{4}'  # Specific for the Lupin format
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # If not found in text, try to construct from filename
        return self._extract_date_from_filename(filename)
    
    def _extract_date_from_filename(self, filename):
        """Extract or construct date from filename"""
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
        
        filename_lower = filename.lower()
        
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
                if month in ['jan', 'january', 'feb', 'february', 'mar', 'march']:
                    fiscal_year = calendar_year  # Jan-Mar belongs to same FY
                else:
                    fiscal_year = calendar_year + 1  # Apr-Dec belongs to next FY
                
                print(f"  📅 Calendar year: {calendar_year}, Month: {month} → Fiscal Year: {fiscal_year}")
                return str(fiscal_year)
            
            return year
        
        return "Unknown Year"
    
    # Keep all the existing methods for general format
    def _extract_management_team(self, text, company):
        """Extract management team members (general format)"""
        management = []
        
        # Get known management names for the company
        known_names = self.management_names.get(company.lower(), [])
        
        # Look for known management names in text
        for name in known_names:
            if name in text:
                # Try to find their designation
                name_pattern = rf'{re.escape(name)}\s*[–-]\s*([^–\n]+)'
                match = re.search(name_pattern, text)
                if match:
                    position = match.group(1).strip()
                    management.append(f"{name} - {position}")
                else:
                    management.append(f"{name} - Position not specified")
        
        return management if management else ["Management information not found"]
    
    def _extract_moderator(self, text):
        """Extract moderator information (general format)"""
        moderator_patterns = [
            r'MODERATOR:\s*([^\.]+)',
            r'Moderator:\s*([^\n]+)',
            r'moderator.*?([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in moderator_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Moderator information not found"
    
    def _extract_analysts(self, text):
        """Extract analyst information (general format)"""
        analysts = []
        
        # Multiple patterns for analyst introductions
        analyst_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+from\s+([A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[–-]\s*([A-Z][a-zA-Z\s&]+)',
        ]
        
        seen_analysts = set()
        
        for pattern in analyst_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                analyst_name = match[0].strip()
                firm = match[1].strip()
                
                if analyst_name not in seen_analysts and len(analyst_name) > 3:
                    analysts.append({
                        "name": analyst_name,
                        "firm": firm
                    })
                    seen_analysts.add(analyst_name)
        
        return analysts
    
    def _extract_qa_segments_improved(self, text, company):
        """General Q&A extraction"""
        qa_segments = []
        mgmt_names = self.management_names.get(company.lower(), [])
        
        # Simple fallback for general format
        question_patterns = [
            r'([^.]*\?[^?]*?)([A-Z][a-z]+\s+[A-Z][a-z]+):\s*([^?]+)',
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            
            for match in matches:
                if len(match) == 3:
                    question, speaker, answer = match
                    qa_segments.append({
                        "analyst_name": "Unknown Analyst",
                        "analyst_firm": "Unknown Firm",
                        "question": question.strip()[:500],
                        "answers": [{
                            "speaker": speaker.strip(),
                            "response": answer.strip()[:500],
                            "speaker_type": "Management" if any(name in speaker for name in mgmt_names) else "Unknown"
                        }]
                    })
        
        return qa_segments[:10]
    
    def _extract_financial_metrics(self, text):
        """Extract financial metrics"""
        metrics = {}
        
        # Enhanced patterns for better extraction
        patterns = [
            (r'revenue.*?(?:of|at|was)\s*(?:INR|Rs\.?)\s*([0-9,]+)\s*crores?', 'revenue_inr_crores'),
            (r'revenue.*?(?:of|at|was)\s*\$\s*([0-9,]+)\s*million', 'revenue_usd_million'),
            (r'sales.*?(?:of|at|was)\s*(?:INR|Rs\.?)\s*([0-9,]+)\s*crores?', 'sales_inr_crores'),
            (r'growth.*?(?:of|at|was)\s*([0-9]+\.?[0-9]*)\s*%', 'growth_percentage'),
            (r'EBITDA.*?(?:of|at|was)\s*([0-9]+\.?[0-9]*)\s*%', 'ebitda_margin_percentage'),
            (r'EBITDA.*?(?:of|at|was)\s*(?:INR|Rs\.?)\s*([0-9,]+)\s*crores?', 'ebitda_inr_crores'),
            (r'US\$([0-9,]+)\s*million', 'us_sales_usd_million'),
        ]
        
        for pattern, metric_name in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                value = matches[0].replace(',', '')
                metrics[metric_name] = value
        
        return metrics
    
    def _extract_business_highlights(self, text):
        """Extract business highlights and key points"""
        highlights = []
        
        # Enhanced patterns for business highlights
        highlight_patterns = [
            r'(launched.*?(?:product|brand|initiative)[^.]*\.)',
            r'(approved.*?(?:by|from).*?(?:FDA|authority)[^.]*\.)',
            r'(partnership.*?with.*?[^.]*\.)',
            r'(acquired.*?[^.]*\.)',
            r'(expanded.*?(?:presence|operations)[^.]*\.)',
            r'(received.*?approval.*?[^.]*\.)',
            r'(filed.*?(?:ANDA|application)[^.]*\.)',
            r'(commenced.*?(?:supply|production)[^.]*\.)',
            r'(expecting.*?launch.*?[^.]*\.)',
            r'(ramp.*?up.*?[^.]*\.)',
        ]
        
        for pattern in highlight_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 20:
                    clean_highlight = re.sub(r'\s+', ' ', match.strip())
                    if clean_highlight not in highlights:
                        highlights.append(clean_highlight)
        
        return highlights[:15]
    
    def save_to_json(self, data, output_path):
        """Save extracted data to JSON file"""
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
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
    
    # Test with sample PDF
    pdf_path = "data/sample.pdf"
    
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