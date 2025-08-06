import sys
import os
sys.path.append('pdf-parser')  # Add pdf-parser to path

from extractor.pdf_extractor import extract_text
from cleaner.text_cleaner import clean_text
from parser.transcript_parser import parse_transcript
import json
from pathlib import Path

def process_pdf(pdf_path, company_name):
    """Process single PDF file"""
    try:
        # Extract
        print(f"    - Extracting text...")
        raw_text = extract_text(pdf_path)
        
        # Clean
        print(f"    - Cleaning text...")
        cleaned_text = clean_text(raw_text)
        
        # Parse
        print(f"    - Parsing dialogue...")
        speakers, dialogue = parse_transcript(cleaned_text)
        
        # Create result
        result = {
            "metadata": {
                "filename": os.path.basename(pdf_path),
                "company": company_name,
                "total_speakers": len(speakers),
                "speakers_list": speakers,
                "total_exchanges": len(dialogue)
            },
            "dialogue": dialogue
        }
        
        return result
    except Exception as e:
        print(f"    Error in process_pdf: {str(e)}")
        raise

def save_json_safely(data, output_path):
    """Save JSON with proper encoding and formatting"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save with proper encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, separators=(',', ': '))
        
        # Verify the JSON was saved correctly
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)  # This will raise an error if JSON is invalid
        
        return True
    except json.JSONDecodeError as e:
        print(f"    JSON Error: {e}")
        return False
    except Exception as e:
        print(f"    Save Error: {e}")
        return False

def main():
    """Process all PDFs in data folder"""
    data_dir = "data"
    output_dir = "output"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if data directory exists
    if not os.path.exists(data_dir):
        print(f"Error: '{data_dir}' folder not found!")
        print("Please create 'data' folder and add company folders with PDFs")
        return
    
    # Process each company folder
    companies = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    if not companies:
        print("No company folders found in data directory!")
        return
    
    print(f"Found {len(companies)} company folder(s): {', '.join(companies)}")
    print("-" * 60)
    
    for company in companies:
        company_path = os.path.join(data_dir, company)
        print(f"\nProcessing {company.upper()}...")
        
        # Create company output folder
        company_output = os.path.join(output_dir, company)
        os.makedirs(company_output, exist_ok=True)
        
        # Get all PDFs in company folder
        pdf_files = [f for f in os.listdir(company_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"  No PDF files found in {company_path}")
            continue
        
        print(f"  Found {len(pdf_files)} PDF file(s)")
        
        # Process each PDF
        success_count = 0
        for pdf_file in pdf_files:
            pdf_path = os.path.join(company_path, pdf_file)
            print(f"\n  Processing: {pdf_file}")
            
            try:
                # Process PDF
                result = process_pdf(pdf_path, company.upper())
                
                # Print summary
                print(f"    - Found {len(result['metadata']['speakers_list'])} speakers")
                print(f"    - Extracted {len(result['dialogue'])} dialogue exchanges")
                
                # Save JSON
                output_file = Path(pdf_file).stem + ".json"
                output_path = os.path.join(company_output, output_file)
                
                if save_json_safely(result, output_path):
                    print(f"    ✓ Saved: {output_path}")
                    success_count += 1
                else:
                    print(f"    ✗ Failed to save valid JSON")
                    
                    # Try to save a debug version
                    debug_path = os.path.join(company_output, Path(pdf_file).stem + "_debug.txt")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(str(result))
                    print(f"    Debug output saved to: {debug_path}")
                    
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
        
        print(f"\n  Completed: {success_count}/{len(pdf_files)} files processed successfully")
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")

if __name__ == "__main__":
    main()