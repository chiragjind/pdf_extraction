import json
import os
import re

class SimpleFilter:
    def __init__(self):
        # Content to remove (case insensitive)
        self.remove_keywords = [
            "good day and welcome",
            "please signal an operator",
            "press '*' then '0'",
            "this conference is being recorded",
            "thank you and over to you",
            "scrip code",
            "company secretary",
            "corporate identity number",
            "regd. office",
            "phone +91",
            "fax +91",
            "e-mail contactus@",
            "website www."
        ]
        
        # Speakers to remove completely
        self.remove_speakers = [
            "Scrip Code",
            "Company Secretary",
            "Operator"
        ]
        
        # Keep these even if short
        self.always_keep_speakers = [
            "MANAGEMENT"  # Executive rosters
        ]
    
    def should_remove_content(self, content):
        """Check if content should be removed"""
        content_lower = content.lower()
        
        # Remove if contains admin keywords
        for keyword in self.remove_keywords:
            if keyword in content_lower:
                return True
        
        # Remove very short responses (< 10 words) unless important
        if len(content.split()) < 10:
            return True
            
        return False
    
    def should_remove_speaker(self, speaker):
        """Check if speaker should be removed"""
        return speaker in self.remove_speakers
    
    def filter_document(self, doc):
        """Filter a single document"""
        speaker = doc.get('metadata', {}).get('speaker', '')
        content = doc.get('content', '')
        
        # Always keep MANAGEMENT speaker (executive rosters)
        if speaker in self.always_keep_speakers:
            return doc
        
        # Remove unwanted speakers
        if self.should_remove_speaker(speaker):
            return None
        
        # Remove unwanted content
        if self.should_remove_content(content):
            return None
        
        return doc
    
    def filter_company_data(self, input_file, output_file):
        """Filter complete company data file"""
        print(f"📂 Processing: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_docs = 0
        kept_docs = 0
        
        # Filter each category
        for category_name, category_data in data['categories'].items():
            original_docs = category_data.get('documents', [])
            filtered_docs = []
            
            for doc in original_docs:
                filtered_doc = self.filter_document(doc)
                if filtered_doc:
                    filtered_docs.append(filtered_doc)
                    kept_docs += 1
                total_docs += 1
            
            # Update category data
            category_data['documents'] = filtered_docs
            category_data['total_documents'] = len(filtered_docs)
            
            print(f"  📋 {category_name}: {len(original_docs)} → {len(filtered_docs)}")
        
        # Update summary stats
        data['summary_stats'] = {
            category: data['categories'][category]['total_documents'] 
            for category in data['categories']
        }
        
        # Save filtered data
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Filtered: {total_docs} → {kept_docs} documents ({kept_docs/total_docs*100:.1f}% kept)")
        print(f"💾 Saved: {output_file}\n")
        
        return data

def main():
    """Filter all company data"""
    filter_obj = SimpleFilter()
    
    # Input and output directories
    input_dir = "rag_ready_results/complete"
    output_dir = "rag_ready_results/filtered"
    
    # Check input directory
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Get all complete files
    complete_files = [f for f in os.listdir(input_dir) if f.endswith('_complete.json')]
    
    if not complete_files:
        print(f"❌ No complete files found in {input_dir}")
        return
    
    print(f"🚀 Found {len(complete_files)} files to filter")
    print("-" * 50)
    
    for file_name in complete_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, file_name.replace('_complete.json', '_filtered.json'))
        
        try:
            filter_obj.filter_company_data(input_path, output_path)
        except Exception as e:
            print(f"❌ Error processing {file_name}: {str(e)}")
    
    print("🎉 Filtering complete!")
    print(f"📁 Filtered files saved in: {output_dir}/")

if __name__ == "__main__":
    main()