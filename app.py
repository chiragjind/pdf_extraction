#!/usr/bin/env python3
"""
PDF Data Extraction App - Production Ready
Extracts structured data from earnings call PDFs from multiple companies
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import json

try:
    from earnings_extractor import EarningsCallExtractor
except ImportError:
    print("❌ Error: earnings_extractor.py not found!")
    print("Please make sure earnings_extractor.py is in the same directory as app.py")
    sys.exit(1)

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories"""
    directories = [
        'data', 
        'data/cipla', 
        'data/lupin', 
        'data/others',
        'output',
        'output/cipla',    # NEW: Separate folder for Cipla JSONs
        'output/lupin',    # NEW: Separate folder for Lupin JSONs  
        'output/others',   # NEW: Separate folder for other company JSONs
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created/verified directory: {directory}")

def find_pdf_files_by_company():
    """Find all PDF files organized by company"""
    pdf_files = {
        'cipla': [],
        'lupin': [],
        'others': []
    }
    
    data_path = Path('data')
    
    # Cipla PDFs
    cipla_path = data_path / 'cipla'
    if cipla_path.exists():
        pdf_files['cipla'] = list(cipla_path.glob('*.pdf'))
    
    # Lupin PDFs  
    lupin_path = data_path / 'lupin'
    if lupin_path.exists():
        pdf_files['lupin'] = list(lupin_path.glob('*.pdf'))
    
    # Other PDFs in main data folder
    others_path = data_path / 'others'
    if others_path.exists():
        pdf_files['others'] = list(others_path.glob('*.pdf'))
    
    # Also check main data folder
    main_pdfs = [f for f in data_path.glob('*.pdf')]
    pdf_files['others'].extend(main_pdfs)
    
    return pdf_files

def print_file_summary(pdf_files):
    """Print summary of found PDF files"""
    total_files = sum(len(files) for files in pdf_files.values())
    
    print(f"\n📊 PDF Files Summary:")
    print(f"{'='*50}")
    print(f"📄 Total PDF files found: {total_files}")
    
    for company, files in pdf_files.items():
        if files:
            print(f"\n🏢 {company.upper()}:")
            for i, file in enumerate(files, 1):
                print(f"  {i:2d}. {file.name}")
    
    return total_files

def get_output_path_for_company(company, data):
    """Get the correct output folder path for each company"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"{data['company']}_{data['quarter']}_{data['fiscal_year']}_{timestamp}_extracted.json"
    
    # Direct to company-specific folder
    if company.lower() == 'cipla':
        output_path = Path('output') / 'cipla' / output_filename
    elif company.lower() == 'lupin':
        output_path = Path('output') / 'lupin' / output_filename
    else:
        output_path = Path('output') / 'others' / output_filename
    
    return output_path, output_filename

def process_company_pdfs(company, pdf_files, extractor, logger):
    """Process all PDFs for a specific company"""
    if not pdf_files:
        return 0, 0
    
    print(f"\n🔄 Processing {company.upper()} PDFs...")
    print("-" * 40)
    
    successful = 0
    failed = 0
    
    # Process with progress bar
    for pdf_file in tqdm(pdf_files, desc=f"Processing {company.upper()}", unit="file"):
        try:
            logger.info(f"Processing {pdf_file.name}")
            
            # Extract data
            data = extractor.extract_from_pdf(str(pdf_file))
            
            # Ensure company name is set correctly
            if data['company'] == 'UNKNOWN':
                data['company'] = company.upper()
            
            # Get company-specific output path
            output_path, output_filename = get_output_path_for_company(company, data)
            
            # Save data
            if extractor.save_to_json(data, str(output_path)):
                successful += 1
                
                # Print extraction summary
                print(f"\n✅ {pdf_file.name}")
                print(f"   📊 {data['quarter']} {data['fiscal_year']} | Date: {data['report_date']}")
                print(f"   👥 Management: {len(data['management_team'])} | Analysts: {len(data['analysts'])}")
                print(f"   💬 Q&A: {len(data['qa_segments'])} | Metrics: {len(data['key_financial_metrics'])}")
                print(f"   📄 → output/{company.lower()}/{output_filename}")
                
                logger.info(f"Successfully processed {pdf_file.name}")
            else:
                failed += 1
                logger.error(f"Failed to save data for {pdf_file.name}")
            
        except Exception as e:
            failed += 1
            error_msg = f"Error processing {pdf_file.name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            logger.error(error_msg)
    
    return successful, failed

def generate_summary_report(all_results):
    """Generate a summary report of all extractions"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = Path('output') / f"extraction_summary_{timestamp}.json"
    
    total_successful = sum(result[0] for result in all_results.values())
    total_failed = sum(result[1] for result in all_results.values())
    total_files = total_successful + total_failed
    
    summary = {
        "extraction_summary": {
            "timestamp": datetime.now().isoformat(),
            "total_files_processed": total_files,
            "successful_extractions": total_successful,
            "failed_extractions": total_failed,
            "success_rate": f"{(total_successful/total_files*100):.1f}%" if total_files > 0 else "0%"
        },
        "company_breakdown": {}
    }
    
    for company, (successful, failed) in all_results.items():
        if successful > 0 or failed > 0:
            summary["company_breakdown"][company] = {
                "successful": successful,
                "failed": failed,
                "total": successful + failed,
                "output_folder": f"output/{company.lower()}/"
            }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Summary report saved: {summary_file}")
    return summary

def main():
    """Main application function"""
    print("🚀 PDF Data Extraction System - Production Ready")
    print("Supports multiple PDFs from Cipla, Lupin, and other companies")
    print("=" * 70)
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting PDF extraction process")
    
    # Setup directories
    setup_directories()
    
    # Initialize extractor
    try:
        extractor = EarningsCallExtractor()
        logger.info("Extractor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        logger.error(f"Failed to initialize extractor: {e}")
        return
    
    # Find PDF files by company
    pdf_files = find_pdf_files_by_company()
    total_files = print_file_summary(pdf_files)
    
    if total_files == 0:
        print("\n❌ No PDF files found!")
        print("\n📋 To get started:")
        print("1. Add Cipla PDFs to 'data/cipla/' folder")
        print("2. Add Lupin PDFs to 'data/lupin/' folder") 
        print("3. Add other company PDFs to 'data/others/' folder")
        print("4. Run this script again")
        logger.warning("No PDF files found to process")
        return
    
    # Process PDFs by company
    print(f"\n🔄 Starting extraction of {total_files} PDF file(s)...")
    
    all_results = {}
    
    for company, files in pdf_files.items():
        if files:
            successful, failed = process_company_pdfs(company, files, extractor, logger)
            all_results[company] = (successful, failed)
    
    # Generate final summary
    print("\n" + "=" * 70)
    print("🎉 EXTRACTION COMPLETE!")
    
    summary = generate_summary_report(all_results)
    
    print(f"\n📊 Final Results:")
    print(f"   ✅ Successful: {summary['extraction_summary']['successful_extractions']}")
    print(f"   ❌ Failed: {summary['extraction_summary']['failed_extractions']}")
    print(f"   📈 Success Rate: {summary['extraction_summary']['success_rate']}")
    
    print(f"\n📁 Output files organized by company:")
    print(f"   🏢 Cipla JSONs: ./output/cipla/")
    print(f"   🏢 Lupin JSONs: ./output/lupin/")
    print(f"   🏢 Others JSONs: ./output/others/")
    print(f"📝 Logs saved in: ./logs/")
    
    if summary['extraction_summary']['successful_extractions'] > 0:
        print(f"\n🎯 Next Steps:")
        print(f"1. Review extracted JSON files in company-specific output folders")
        print(f"2. Check logs for any processing details")
        print(f"3. Use JSON data for analysis or integration")
    
    logger.info("PDF extraction process completed")

if __name__ == "__main__":
    main()