#!/usr/bin/env python3
"""
Simple test script for PDF extraction system
"""

import json
from pathlib import Path

# Test import first
try:
    from earnings_extractor import EarningsCallExtractor
    print("✅ Successfully imported EarningsCallExtractor")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
except SyntaxError as e:
    print(f"❌ Syntax error in earnings_extractor.py: {e}")
    exit(1)

def find_test_pdf():
    """Find a PDF file to test with"""
    # Check various locations
    search_paths = [
        'data/cipla/*.pdf',
        'data/lupin/*.pdf', 
        'data/others/*.pdf',
        'data/*.pdf'
    ]
    
    for path_pattern in search_paths:
        files = list(Path('.').glob(path_pattern))
        if files:
            return files[0]
    
    return None

def quick_test():
    """Quick test of the extraction system"""
    print("🧪 Quick PDF Extraction Test")
    print("=" * 40)
    
    # Find a test PDF
    test_pdf = find_test_pdf()
    
    if not test_pdf:
        print("❌ No PDF files found!")
        print("\n📋 Please add a PDF file to one of these folders:")
        print("   - data/cipla/")
        print("   - data/lupin/")
        print("   - data/others/")
        return
    
    print(f"📄 Testing with: {test_pdf}")
    
    # Initialize extractor
    try:
        extractor = EarningsCallExtractor()
        print("✅ Extractor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return
    
    # Extract data
    try:
        print("\n🔄 Starting extraction...")
        data = extractor.extract_from_pdf(str(test_pdf))
        print("✅ Extraction completed")
        
        # Print key results
        print(f"\n📊 Results Summary:")
        print(f"   Company: {data['company']}")
        print(f"   Quarter: {data['quarter']} FY{data['fiscal_year']}")
        print(f"   Management: {len(data['management_team'])} members")
        print(f"   Analysts: {len(data['analysts'])} found")
        print(f"   Q&A Segments: {len(data['qa_segments'])} found")
        print(f"   Financial Metrics: {len(data['key_financial_metrics'])} found")
        
        # Show first Q&A segment if exists
        if data['qa_segments']:
            print(f"\n💬 Sample Q&A:")
            qa = data['qa_segments'][0]
            print(f"   Analyst: {qa['analyst_name']} from {qa['analyst_firm']}")
            question_preview = qa['question'][:100] + "..." if len(qa['question']) > 100 else qa['question']
            print(f"   Question: {question_preview}")
            print(f"   Answers: {len(qa['answers'])} responses")
            
            for answer in qa['answers'][:2]:
                response_preview = answer['response'][:60] + "..." if len(answer['response']) > 60 else answer['response']
                print(f"      {answer['speaker']}: {response_preview}")
        
        # Create test output
        output_dir = Path('output/test')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"test_extraction_{data['company']}.json"
        
        if extractor.save_to_json(data, str(output_file)):
            print(f"\n✅ Test results saved to: {output_file}")
        
        print(f"\n🎯 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()