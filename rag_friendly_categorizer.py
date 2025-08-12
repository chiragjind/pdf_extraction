import json
import re
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import glob

class RAGFriendlyEarningsCallCategorizer:
    def __init__(self):
        # Define category keywords
        self.categories = {
            "Financial Performance": [
                "revenue", "earnings", "margin", "profit", "cash flow", "beat", "miss", 
                "ebitda", "sales", "assets", "debt", "loan", "growth", "decline", 
                "income", "expenses", "costs", "financial", "performance", "turnover",
                "operating profit", "net profit", "gross margin", "operating margin"
            ],
            
            "Guidance & Outlook": [
                "outlook", "forecast", "expect", "guidance", "macro", "headwinds", 
                "future", "forward", "next quarter", "fy", "projections", "estimates", 
                "target", "goal", "anticipate", "predict", "going forward", "ahead"
            ],
            
            "Operational Updates": [
                "supply chain", "production", "capacity", "market share", "expansion", 
                "capex", "operations", "manufacturing", "facility", "plant", 
                "efficiency", "utilization", "volume", "capacity utilization"
            ],
            
            "Risks & Challenges": [
                "risk", "headwind", "challenge", "uncertainty", "volatility", 
                "slowdown", "difficulty", "shortages", "compliance", "inflation", 
                "geopolitics", "regulatory", "competition", "threat", "pressure"
            ],
            
            "Capital Allocation": [
                "dividend", "buyback", "repurchase", "acquisition", "investment", 
                "capital allocation", "m&a", "merger", "divestiture", "stake", 
                "share repurchase", "payout", "capex", "capital expenditure"
            ],
            
            "Innovation & R&D": [
                "r&d", "innovation", "launch", "entering", "product pipeline", 
                "expanding", "development", "research", "new product", "technology", 
                "patent", "intellectual property", "product development", "clinical trials"
            ],
            
            "Healthcare Specific": [
                "fda approval", "api", "drug", "pharmaceutical", "clinical trials", 
                "regulatory approval", "medical", "therapy", "treatment", "dosage", 
                "medicine", "usfda", "who gmp", "dmf", "anda", "biosimilar", 
                "generic", "branded", "chronic", "acute", "respiratory", "oncology"
            ],
            
            "Market & Competition": [
                "market share", "competition", "competitive", "pricing", "tender", 
                "market penetration", "distribution", "channel", "brand", "portfolio",
                "market dynamics", "competitive landscape"
            ],
            
            "Regulatory & Compliance": [
                "regulatory", "compliance", "fda", "who", "gmp", "inspection", 
                "approval", "filing", "submission", "regulatory pathway", "cdsco"
            ],
            
            "International Business": [
                "us market", "europe", "international", "export", "global", 
                "overseas", "foreign", "emerging markets", "developed markets",
                "geography", "regions"
            ]
        }
        
        # Compile regex patterns for better performance
        self.category_patterns = {}
        for category, keywords in self.categories.items():
            pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\b'
            self.category_patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def extract_date_from_filename(self, filename):
        """Extract date from filename patterns"""
        name = Path(filename).stem
        
        # Pattern 1: Month_Year (e.g., Aug_2018)
        month_year_match = re.search(r'([A-Za-z]{3,9})_(\d{4})', name)
        if month_year_match:
            month_str, year = month_year_match.groups()
            try:
                month_num = datetime.strptime(month_str[:3], '%b').month
                return datetime(int(year), month_num, 1)
            except ValueError:
                pass
        
        # Pattern 2: Q1_FY19 format
        quarter_fy_match = re.search(r'Q(\d)_FY(\d{2,4})', name, re.IGNORECASE)
        if quarter_fy_match:
            quarter, fy_year = quarter_fy_match.groups()
            if len(fy_year) == 2:
                fy_year = int('20' + fy_year) if int(fy_year) < 50 else int('19' + fy_year)
            else:
                fy_year = int(fy_year)
            
            quarter_months = {1: 4, 2: 7, 3: 10, 4: 1}
            month = quarter_months[int(quarter)]
            year = fy_year if month != 1 else fy_year + 1
            return datetime(year, month, 1)
        
        # Pattern 3: Just year
        year_match = re.search(r'(\d{4})', name)
        if year_match:
            return datetime(int(year_match.group(1)), 1, 1)
        
        return datetime.now()
    
    def categorize_dialogue(self, dialogue_entry):
        """Categorize a single dialogue entry"""
        text = dialogue_entry.get('text', '').lower()
        categories_found = []
        
        for category, pattern in self.category_patterns.items():
            if pattern.search(text):
                categories_found.append(category)
        
        return categories_found if categories_found else ["General"]
    
    def create_rag_document(self, dialogue_entry, metadata):
        """Create a RAG-friendly document chunk"""
        return {
            "id": f"{metadata['company']}_{metadata['date']}_{dialogue_entry['speaker'][:10]}_{hash(dialogue_entry['text'][:50]) % 10000}",
            "content": dialogue_entry['text'],
            "metadata": {
                "company": metadata['company'],
                "speaker": dialogue_entry['speaker'],
                "date": metadata['date'],
                "source_file": metadata['source_file'],
                "quarter": metadata.get('quarter', ''),
                "fiscal_year": metadata.get('fiscal_year', ''),
                "speaker_role": self.get_speaker_role(dialogue_entry['speaker']),
                "content_length": len(dialogue_entry['text']),
                "word_count": len(dialogue_entry['text'].split())
            }
        }
    
    def get_speaker_role(self, speaker_name):
        """Determine speaker role based on name patterns"""
        speaker_lower = speaker_name.lower()
        
        if any(title in speaker_lower for title in ['ceo', 'chief executive']):
            return "CEO"
        elif any(title in speaker_lower for title in ['cfo', 'chief financial']):
            return "CFO"
        elif any(title in speaker_lower for title in ['coo', 'chief operating']):
            return "COO"
        elif any(title in speaker_lower for title in ['md', 'managing director']):
            return "MD"
        elif 'moderator' in speaker_lower:
            return "Moderator"
        elif 'management' in speaker_lower:
            return "Management"
        else:
            return "Analyst/Other"
    
    def extract_quarter_and_fy(self, filename, date):
        """Extract quarter and FY information"""
        name = filename.lower()
        
        # Extract quarter
        quarter_match = re.search(r'q(\d)', name)
        quarter = f"Q{quarter_match.group(1)}" if quarter_match else ""
        
        # Extract FY
        fy_match = re.search(r'fy(\d{2,4})', name)
        if fy_match:
            fy_year = fy_match.group(1)
            fiscal_year = f"FY{fy_year}" if len(fy_year) == 2 else f"FY{fy_year[-2:]}"
        else:
            # Derive FY from date (assuming April-March FY)
            if date.month >= 4:
                fiscal_year = f"FY{str(date.year + 1)[-2:]}"
            else:
                fiscal_year = f"FY{str(date.year)[-2:]}"
        
        return quarter, fiscal_year
    
    def process_company_data(self, company_folder):
        """Process all JSON files for a company and organize by category"""
        json_files = glob.glob(os.path.join(company_folder, "*.json"))
        
        if not json_files:
            print(f"No JSON files found in {company_folder}")
            return None
        
        company_name = os.path.basename(company_folder).upper()
        
        # Initialize category-wise storage
        categories_data = {}
        for category in self.categories.keys():
            categories_data[category] = {
                "category_name": category,
                "category_keywords": self.categories[category],
                "documents": [],
                "total_documents": 0,
                "date_range": {"earliest": None, "latest": None},
                "speakers": set(),
                "source_files": set()
            }
        
        # Add General category
        categories_data["General"] = {
            "category_name": "General",
            "category_keywords": [],
            "documents": [],
            "total_documents": 0,
            "date_range": {"earliest": None, "latest": None},
            "speakers": set(),
            "source_files": set()
        }
        
        all_dates = []
        
        # Process each file
        for json_file in sorted(json_files):
            print(f"Processing: {os.path.basename(json_file)}")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                filename = os.path.basename(json_file)
                extracted_date = self.extract_date_from_filename(filename)
                quarter, fiscal_year = self.extract_quarter_and_fy(filename, extracted_date)
                all_dates.append(extracted_date)
                
                file_metadata = {
                    "company": company_name,
                    "source_file": filename,
                    "date": extracted_date.isoformat(),
                    "quarter": quarter,
                    "fiscal_year": fiscal_year
                }
                
                # Process each dialogue entry
                for dialogue_entry in data.get('dialogue', []):
                    categories = self.categorize_dialogue(dialogue_entry)
                    rag_document = self.create_rag_document(dialogue_entry, file_metadata)
                    
                    # Add to each relevant category
                    for category in categories:
                        if category in categories_data:
                            categories_data[category]["documents"].append(rag_document)
                            categories_data[category]["speakers"].add(dialogue_entry['speaker'])
                            categories_data[category]["source_files"].add(filename)
                            
                            # Update date range
                            if categories_data[category]["date_range"]["earliest"] is None:
                                categories_data[category]["date_range"]["earliest"] = extracted_date.isoformat()
                                categories_data[category]["date_range"]["latest"] = extracted_date.isoformat()
                            else:
                                if extracted_date.isoformat() < categories_data[category]["date_range"]["earliest"]:
                                    categories_data[category]["date_range"]["earliest"] = extracted_date.isoformat()
                                if extracted_date.isoformat() > categories_data[category]["date_range"]["latest"]:
                                    categories_data[category]["date_range"]["latest"] = extracted_date.isoformat()
            
            except Exception as e:
                print(f"Error processing {json_file}: {str(e)}")
                continue
        
        # Finalize the data
        for category in categories_data:
            # Sort documents by date
            categories_data[category]["documents"].sort(key=lambda x: x["metadata"]["date"])
            categories_data[category]["total_documents"] = len(categories_data[category]["documents"])
            categories_data[category]["speakers"] = list(categories_data[category]["speakers"])
            categories_data[category]["source_files"] = list(categories_data[category]["source_files"])
            
            # Remove empty categories
            if categories_data[category]["total_documents"] == 0:
                categories_data[category] = None
        
        # Remove None categories
        categories_data = {k: v for k, v in categories_data.items() if v is not None}
        
        # Create final structure
        final_data = {
            "company": company_name,
            "processing_date": datetime.now().isoformat(),
            "total_files_processed": len(json_files),
            "date_range": {
                "earliest": min(all_dates).isoformat() if all_dates else None,
                "latest": max(all_dates).isoformat() if all_dates else None
            },
            "total_categories": len(categories_data),
            "categories": categories_data,
            "summary_stats": {
                category: data["total_documents"] 
                for category, data in categories_data.items()
            }
        }
        
        return final_data
    
    def create_category_specific_files(self, company_data, results_dir):
        """Create separate files for each category"""
        company_name = company_data["company"].lower()
        category_files_created = []
        
        for category_name, category_data in company_data["categories"].items():
            if category_data["total_documents"] > 0:
                # Create category-specific file
                category_filename = f"{company_name}_{category_name.lower().replace(' & ', '_').replace(' ', '_')}.json"
                category_file_path = os.path.join(results_dir, "by_category", category_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(category_file_path), exist_ok=True)
                
                # Prepare category file content
                category_file_content = {
                    "company": company_data["company"],
                    "category": category_name,
                    "category_keywords": category_data["category_keywords"],
                    "total_documents": category_data["total_documents"],
                    "date_range": category_data["date_range"],
                    "speakers_involved": category_data["speakers"],
                    "source_files": category_data["source_files"],
                    "documents": category_data["documents"],
                    "created_date": datetime.now().isoformat()
                }
                
                with open(category_file_path, 'w', encoding='utf-8') as f:
                    json.dump(category_file_content, f, indent=2, ensure_ascii=False)
                
                category_files_created.append(category_file_path)
                print(f"✓ Created category file: {category_filename}")
        
        return category_files_created
    
    def create_embeddings_ready_format(self, company_data, results_dir):
        """Create a format ready for embeddings/vector database"""
        company_name = company_data["company"].lower()
        
        # Flatten all documents with their categories
        embeddings_data = []
        
        for category_name, category_data in company_data["categories"].items():
            for doc in category_data["documents"]:
                embedding_doc = {
                    "id": doc["id"],
                    "text": doc["content"],
                    "metadata": {
                        **doc["metadata"],
                        "category": category_name,
                        "category_keywords": category_data["category_keywords"]
                    }
                }
                embeddings_data.append(embedding_doc)
        
        # Save embeddings-ready file
        embeddings_file = os.path.join(results_dir, "embeddings", f"{company_name}_embeddings_ready.json")
        os.makedirs(os.path.dirname(embeddings_file), exist_ok=True)
        
        embeddings_content = {
            "company": company_data["company"],
            "total_documents": len(embeddings_data),
            "created_date": datetime.now().isoformat(),
            "documents": embeddings_data
        }
        
        with open(embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_content, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Created embeddings file: {company_name}_embeddings_ready.json")
        return embeddings_file

def main():
    """Main function to process all companies"""
    categorizer = RAGFriendlyEarningsCallCategorizer()
    output_base_dir = "output"
    results_dir = "rag_ready_results"
    
    # Create results directory structure
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(os.path.join(results_dir, "by_category"), exist_ok=True)
    os.makedirs(os.path.join(results_dir, "embeddings"), exist_ok=True)
    os.makedirs(os.path.join(results_dir, "complete"), exist_ok=True)
    
    # Get all company folders
    company_folders = [
        os.path.join(output_base_dir, d) 
        for d in os.listdir(output_base_dir) 
        if os.path.isdir(os.path.join(output_base_dir, d))
    ]
    
    if not company_folders:
        print("No company folders found in output directory!")
        return
    
    print(f"Found {len(company_folders)} company folder(s)")
    print("-" * 80)
    
    all_company_summaries = []
    
    for company_folder in company_folders:
        company_name = os.path.basename(company_folder).upper()
        print(f"\n🏢 Processing {company_name}...")
        
        # Process company data
        company_data = categorizer.process_company_data(company_folder)
        
        if company_data:
            # 1. Save complete company data
            complete_file = os.path.join(results_dir, "complete", f"{company_name.lower()}_complete.json")
            with open(complete_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved complete data: {complete_file}")
            
            # 2. Create category-specific files
            category_files = categorizer.create_category_specific_files(company_data, results_dir)
            
            # 3. Create embeddings-ready format
            embeddings_file = categorizer.create_embeddings_ready_format(company_data, results_dir)
            
            # 4. Print summary
            print(f"\n📊 {company_name} Summary:")
            print(f"  - Total categories with data: {company_data['total_categories']}")
            print(f"  - Date range: {company_data['date_range']['earliest'][:10]} to {company_data['date_range']['latest'][:10]}")
            print(f"  - Top 3 categories:")
            
            sorted_categories = sorted(company_data['summary_stats'].items(), key=lambda x: x[1], reverse=True)
            for i, (cat, count) in enumerate(sorted_categories[:3], 1):
                print(f"    {i}. {cat}: {count} documents")
            
            # Add to summary
            company_summary = {
                "company": company_name,
                "total_documents": sum(company_data['summary_stats'].values()),
                "categories": company_data['summary_stats'],
                "date_range": company_data['date_range'],
                "files_created": {
                    "complete_file": complete_file,
                    "embeddings_file": embeddings_file,
                    "category_files": len(category_files)
                }
            }
            all_company_summaries.append(company_summary)
    
    # Create master summary
    master_summary = {
        "processing_date": datetime.now().isoformat(),
        "total_companies": len(all_company_summaries),
        "companies": all_company_summaries,
        "directory_structure": {
            "complete/": "Complete company data files",
            "by_category/": "Individual category files for each company",
            "embeddings/": "Vector database ready format"
        }
    }
    
    summary_file = os.path.join(results_dir, "master_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(master_summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("🎉 RAG-Ready Processing Complete!")
    print(f"📁 Results saved in: {results_dir}/")
    print("\n📂 Directory Structure:")
    print("├── complete/           - Complete company data")
    print("├── by_category/        - Individual category files")  
    print("├── embeddings/         - Vector database ready format")
    print("└── master_summary.json - Processing summary")
    print("\n💡 For RAG chatbot:")
    print("- Use files in 'by_category/' for category-specific retrieval")
    print("- Use files in 'embeddings/' for vector database ingestion")
    print("- Each category file contains all related dialogue grouped together")

if __name__ == "__main__":
    main()