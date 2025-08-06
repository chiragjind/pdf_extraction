import json
import re
import PyPDF2
import pdfplumber
from typing import List, Dict, Any
import os
from pathlib import Path
from datetime import datetime

class PDFTranscriptParser:
    """
    Enhanced parser for converting PDF conference call transcripts to structured JSON format.
    Handles various PDF encoding issues and maintains proper speaker identification.
    """
    
    def __init__(self):
        # More flexible speaker patterns
        self.speaker_patterns = [
            r'^([A-Z][a-zA-Z\s\.\-]+?):\s*(.*)$',  # Standard: "Name: text"
            r'^Moderator:\s*(.*)$',  # Moderator pattern
            r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+):\s*(.*)$',  # Full names
        ]
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF with multiple fallback methods.
        """
        text = ""
        
        # Try pdfplumber first
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    return text
        except Exception as e:
            print(f"    pdfplumber failed: {e}")
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            print(f"    PyPDF2 failed: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def fix_character_spacing(self, text: str) -> str:
        """
        Fix text where each character is separated by quotes or spaces.
        Example: '''H'''e'''l'''l'''o''' -> Hello
        """
        # Remove triple quotes between characters
        text = re.sub(r"'''", "", text)
        
        # If text still has issues, try another approach
        if "'" in text and len(text) > len(text.replace("'", "")) * 2:
            # Remove all single quotes that appear to be separators
            text = re.sub(r"'([a-zA-Z0-9])'", r"\1", text)
            text = re.sub(r"'", "", text)
        
        return text
    
    def clean_text(self, text: str) -> str:
        """
        Enhanced text cleaning to handle various PDF encoding issues.
        """
        # First, fix character spacing issues
        text = self.fix_character_spacing(text)
        
        # Remove page headers/footers
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)  # Remove standalone page numbers
        
        # Fix common encoding issues
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('–', '-').replace('—', '-')
        
        # Clean up excessive whitespace while preserving paragraph breaks
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'\t+', ' ', text)  # Tabs to spaces
        
        # Remove any remaining artifacts
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII that might cause issues
        
        return text.strip()
    
    def extract_speakers_from_header(self, text: str) -> List[str]:
        """
        Extract speaker names from the header/management section of transcript.
        """
        speakers = []
        
        # Look for MANAGEMENT: section
        management_match = re.search(r'MANAGEMENT[:\s]+(.*?)(?:MODERATOR|Page|\n\n)', text, re.IGNORECASE | re.DOTALL)
        if management_match:
            management_text = management_match.group(1)
            # Extract names (usually in format: MR./MS./DR. NAME - TITLE)
            name_pattern = r'(?:MR\.|MS\.|DR\.)\s*([A-Z][A-Z\s\.]+?)(?:\s*[-–]\s*|,|\n)'
            names = re.findall(name_pattern, management_text, re.IGNORECASE)
            speakers.extend([name.strip() for name in names])
        
        # Look for MODERATOR: section
        moderator_match = re.search(r'MODERATOR[:\s]+(?:MR\.|MS\.|DR\.)?\s*([A-Z][A-Z\s\.]+?)(?:\s*[-–]|\n)', text, re.IGNORECASE)
        if moderator_match:
            speakers.append(moderator_match.group(1).strip())
        
        return speakers
    
    def identify_speakers(self, text: str) -> List[str]:
        """
        Enhanced speaker identification from the transcript.
        """
        speakers = set()
        
        # First try to get speakers from header
        header_speakers = self.extract_speakers_from_header(text)
        speakers.update(header_speakers)
        
        # Split into lines for line-by-line analysis
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a potential speaker name followed by colon
            # Pattern: "Name Name:" or "Title Name:" at the beginning of a line
            match = re.match(r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s*:', line)
            if match:
                potential_speaker = match.group(1).strip()
                # Filter out common non-speaker words
                if (len(potential_speaker) > 2 and 
                    potential_speaker.lower() not in ['page', 'august', 'january', 'february', 'march', 
                                                     'april', 'may', 'june', 'july', 'september', 
                                                     'october', 'november', 'december', 'monday',
                                                     'tuesday', 'wednesday', 'thursday', 'friday',
                                                     'saturday', 'sunday', 'question', 'answer']):
                    speakers.add(potential_speaker)
            
            # Special check for "Moderator"
            if line.startswith('Moderator:'):
                speakers.add('Moderator')
        
        # Clean up speaker names
        cleaned_speakers = []
        for speaker in speakers:
            # Remove titles if they're included
            speaker = re.sub(r'^(MR\.|MS\.|DR\.)\s*', '', speaker, flags=re.IGNORECASE)
            speaker = speaker.strip()
            if speaker:
                cleaned_speakers.append(speaker)
        
        return sorted(list(set(cleaned_speakers)))
    
    def parse_transcript(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse the transcript into structured dialogue format with improved speaker detection.
        """
        dialogue = []
        current_speaker = None
        current_text = []
        
        # Split text into lines
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for speaker at beginning of line
            speaker_found = False
            
            # Check for Moderator
            if line.startswith('Moderator:'):
                # Save previous speaker's text
                if current_speaker and current_text:
                    combined_text = ' '.join(current_text).strip()
                    if combined_text:
                        dialogue.append({
                            "speaker": current_speaker,
                            "text": combined_text
                        })
                
                current_speaker = "Moderator"
                remaining_text = line[10:].strip()  # Remove "Moderator:" prefix
                current_text = [remaining_text] if remaining_text else []
                speaker_found = True
            
            # Check for other speakers (Name Name:)
            if not speaker_found:
                # More flexible pattern for names
                match = re.match(r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s*:\s*(.*)$', line)
                if match:
                    potential_speaker = match.group(1).strip()
                    
                    # Validate it's likely a speaker name
                    if (len(potential_speaker) > 2 and 
                        len(potential_speaker.split()) <= 4 and  # Most names are 1-4 words
                        potential_speaker.lower() not in ['page', 'august', 'january', 'february', 
                                                         'march', 'april', 'may', 'june', 'july', 
                                                         'september', 'october', 'november', 'december',
                                                         'question', 'answer', 'thank you']):
                        
                        # Save previous speaker's text
                        if current_speaker and current_text:
                            combined_text = ' '.join(current_text).strip()
                            if combined_text:
                                dialogue.append({
                                    "speaker": current_speaker,
                                    "text": combined_text
                                })
                        
                        current_speaker = potential_speaker
                        remaining_text = match.group(2).strip()
                        current_text = [remaining_text] if remaining_text else []
                        speaker_found = True
            
            # If no speaker found, add to current speaker's text
            if not speaker_found:
                if current_speaker:
                    current_text.append(line)
                elif not dialogue and i < 10:  # First few lines without speaker
                    # This might be a header or introduction
                    if 'conference call' in line.lower() or 'earnings' in line.lower():
                        dialogue.append({
                            "speaker": "Introduction",
                            "text": line
                        })
        
        # Don't forget the last speaker's text
        if current_speaker and current_text:
            combined_text = ' '.join(current_text).strip()
            if combined_text:
                dialogue.append({
                    "speaker": current_speaker,
                    "text": combined_text
                })
        
        # If no dialogue was parsed, put all text as narrator
        if not dialogue and text.strip():
            dialogue.append({
                "speaker": "Document Text",
                "text": text.strip()[:5000]  # Limit to first 5000 chars for readability
            })
        
        return dialogue
    
    def process_single_pdf(self, pdf_path: str, company_name: str = None) -> Dict[str, Any]:
        """
        Process a single PDF file and return structured JSON data.
        """
        print(f"  Processing: {os.path.basename(pdf_path)}")
        
        try:
            # Extract text
            raw_text = self.extract_text_from_pdf(pdf_path)
            print(f"    Extracted {len(raw_text)} characters")
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            print(f"    Cleaned text: {len(cleaned_text)} characters")
            
            # Show sample of cleaned text for debugging
            if cleaned_text:
                sample = cleaned_text[:200].replace('\n', ' ')
                print(f"    Sample: {sample}...")
            
            # Identify speakers
            speakers = self.identify_speakers(cleaned_text)
            print(f"    Found {len(speakers)} speakers: {speakers[:5]}...")  # Show first 5
            
            # Parse dialogue
            dialogue = self.parse_transcript(cleaned_text)
            print(f"    Parsed {len(dialogue)} dialogue exchanges")
            
            # Create metadata
            metadata = {
                "filename": os.path.basename(pdf_path),
                "company": company_name if company_name else "Unknown",
                "total_speakers": len(speakers),
                "speakers_list": speakers,
                "total_exchanges": len(dialogue),
                "processing_timestamp": str(datetime.now()),
                "text_length": len(cleaned_text)
            }
            
            return {
                "metadata": metadata,
                "dialogue": dialogue
            }
            
        except Exception as e:
            print(f"    ERROR: {str(e)}")
            raise
    
    def process_company_folder(self, company_folder: str, output_base_dir: str = "output") -> Dict[str, Any]:
        """
        Process all PDFs in a company folder and save to company-specific output folder.
        """
        company_name = os.path.basename(company_folder).upper()
        print(f"\n{'='*50}")
        print(f"Processing Company: {company_name}")
        print(f"{'='*50}")
        
        # Get all PDF files in the company folder
        pdf_files = []
        for file in os.listdir(company_folder):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(company_folder, file))
        
        if not pdf_files:
            print(f"  No PDF files found in {company_folder}")
            return {}
        
        print(f"  Found {len(pdf_files)} PDF file(s)")
        
        # Create output directory for this company
        company_output_dir = os.path.join(output_base_dir, company_name)
        os.makedirs(company_output_dir, exist_ok=True)
        
        results = {}
        successful = 0
        failed = 0
        
        for pdf_path in pdf_files:
            try:
                # Process the PDF
                result = self.process_single_pdf(pdf_path, company_name)
                
                # Save individual JSON file
                output_filename = Path(pdf_path).stem + "_parsed.json"
                output_path = os.path.join(company_output_dir, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"    ✓ Saved to: {output_path}")
                results[os.path.basename(pdf_path)] = result
                successful += 1
                
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                results[os.path.basename(pdf_path)] = {"error": str(e)}
                failed += 1
        
        # Save combined JSON for this company
        if results:
            combined_path = os.path.join(company_output_dir, f"{company_name}_all_transcripts.json")
            with open(combined_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n  Combined JSON saved to: {combined_path}")
        
        print(f"  Summary: {successful} successful, {failed} failed")
        
        return results
    
    def process_all_companies(self, data_dir: str = "data", output_dir: str = "output") -> Dict[str, Any]:
        """
        Process all company folders in the data directory.
        """
        print("\n" + "="*60)
        print("PDF TRANSCRIPT PARSER - BATCH PROCESSING")
        print("="*60)
        
        if not os.path.exists(data_dir):
            print(f"Error: Data directory '{data_dir}' not found!")
            return {}
        
        # Get all subdirectories in the data folder
        company_folders = [
            os.path.join(data_dir, d) 
            for d in os.listdir(data_dir) 
            if os.path.isdir(os.path.join(data_dir, d))
        ]
        
        if not company_folders:
            print(f"No company folders found in '{data_dir}'")
            return {}
        
        print(f"Found {len(company_folders)} company folder(s): {', '.join([os.path.basename(f) for f in company_folders])}")
        
        # Create main output directory
        os.makedirs(output_dir, exist_ok=True)
        
        all_results = {}
        
        # Process each company folder
        for company_folder in company_folders:
            company_name = os.path.basename(company_folder)
            company_results = self.process_company_folder(company_folder, output_dir)
            if company_results:
                all_results[company_name] = company_results
        
        # Save master combined file with all companies
        if all_results:
            master_path = os.path.join(output_dir, "all_companies_transcripts.json")
            with open(master_path, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            
            print("\n" + "="*60)
            print(f"PROCESSING COMPLETE!")
            print(f"Master file saved to: {master_path}")
            print(f"Total companies processed: {len(all_results)}")
            print("="*60 + "\n")
        
        return all_results


def main():
    """
    Main function to run the PDF transcript parser.
    """
    # Initialize parser
    parser = PDFTranscriptParser()
    
    # Process all companies in the data folder
    results = parser.process_all_companies(data_dir="data", output_dir="output")
    
    # Print summary
    if results:
        print("\nFinal Summary:")
        for company, company_results in results.items():
            valid_count = sum(1 for r in company_results.values() if 'error' not in r)
            total_speakers = sum(r.get('metadata', {}).get('total_speakers', 0) 
                               for r in company_results.values() if 'error' not in r)
            total_exchanges = sum(r.get('metadata', {}).get('total_exchanges', 0) 
                                for r in company_results.values() if 'error' not in r)
            print(f"  {company}:")
            print(f"    - PDFs processed: {valid_count}/{len(company_results)}")
            print(f"    - Total speakers found: {total_speakers}")
            print(f"    - Total dialogue exchanges: {total_exchanges}")
    else:
        print("\nNo PDFs were processed. Please check your data folder structure.")


if __name__ == "__main__":
    main()