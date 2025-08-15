import json
import os
import re

class ExecutiveExtractor:
    def __init__(self):
        # Patterns to extract names and roles from MANAGEMENT entries
        self.name_patterns = [
            r'(MR\.|MS\.|DR\.)\s*([A-Z][A-Za-z\s\.]+?)\s*[-–]\s*(CEO|CFO|MANAGING DIRECTOR|PRESIDENT|VICE CHAIRMAN|GROUP PRESIDENT)',
            r'([A-Z][A-Za-z\s\.]+?)\s*[-–]\s*(CEO|CFO|MANAGING DIRECTOR|CHIEF EXECUTIVE|CHIEF FINANCIAL)',
            r'(MR\.|MS\.|DR\.)\s*([A-Z][A-Za-z\s\.]+?)\s*[-–]\s*(CHIEF EXECUTIVE|CHIEF FINANCIAL|CHIEF OPERATING)',
        ]
        
        # Executive roles to prioritize
        self.executive_roles = [
            'CEO', 'CFO', 'MANAGING DIRECTOR', 'MD', 'CHIEF EXECUTIVE', 
            'CHIEF FINANCIAL', 'VICE CHAIRMAN', 'GROUP PRESIDENT'
        ]
    
    def extract_names_from_management(self, content):
        """Extract executive names from MANAGEMENT speaker content"""
        executives = {}
        
        for pattern in self.name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:
                    title, name, role = match
                    clean_name = f"{title} {name}".strip()
                else:
                    clean_name, role = match
                
                # Clean the name
                clean_name = re.sub(r'^(MR\.|MS\.|DR\.)\s*', '', clean_name).strip()
                clean_name = re.sub(r'\s+', ' ', clean_name)
                
                # Only keep if it's an executive role
                if any(exec_role in role.upper() for exec_role in self.executive_roles):
                    executives[clean_name] = role.upper()
        
        return executives
    
    def find_executive_dialogue_by_category(self, data, executive_names):
        """Find actual dialogue from executives organized by category"""
        executive_dialogue = {}
        
        # Process each category
        for category_name, category_data in data['categories'].items():
            documents = category_data.get('documents', [])
            
            for doc in documents:
                speaker = doc.get('metadata', {}).get('speaker', '')
                
                # Skip MANAGEMENT roster entries
                if speaker == 'MANAGEMENT':
                    continue
                
                # Check if speaker matches any executive name
                for exec_name in executive_names:
                    if self.name_matches(speaker, exec_name):
                        # Initialize executive if not exists
                        if exec_name not in executive_dialogue:
                            executive_dialogue[exec_name] = {}
                        
                        # Initialize category if not exists
                        if category_name not in executive_dialogue[exec_name]:
                            executive_dialogue[exec_name][category_name] = []
                        
                        # Add executive info to metadata
                        enhanced_doc = doc.copy()
                        enhanced_doc['metadata'] = doc['metadata'].copy()
                        enhanced_doc['metadata']['executive_role'] = executive_names[exec_name]
                        enhanced_doc['metadata']['is_executive'] = True
                        enhanced_doc['metadata']['category'] = category_name
                        
                        executive_dialogue[exec_name][category_name].append(enhanced_doc)
                        break
        
        return executive_dialogue
    
    def name_matches(self, speaker, executive_name):
        """Check if speaker name matches executive name"""
        # Clean both names for comparison
        clean_speaker = re.sub(r'[^\w\s]', '', speaker.upper())
        clean_exec = re.sub(r'[^\w\s]', '', executive_name.upper())
        
        # Check various matching patterns
        speaker_parts = clean_speaker.split()
        exec_parts = clean_exec.split()
        
        # Full name match
        if clean_speaker == clean_exec:
            return True
        
        # Last name match (most common)
        if len(speaker_parts) > 0 and len(exec_parts) > 0:
            if speaker_parts[-1] == exec_parts[-1]:
                return True
        
        # First + Last name match
        if len(speaker_parts) >= 2 and len(exec_parts) >= 2:
            if speaker_parts[0] == exec_parts[0] and speaker_parts[-1] == exec_parts[-1]:
                return True
        
        return False
    
    def process_company_data(self, input_file, output_file):
        """Extract executive dialogue from filtered company data"""
        print(f"📂 Processing: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Step 1: Extract executive names from MANAGEMENT entries
        executives = {}
        
        for category_name, category_data in data['categories'].items():
            documents = category_data.get('documents', [])
            
            # Look for MANAGEMENT entries to extract names
            for doc in documents:
                if doc.get('metadata', {}).get('speaker') == 'MANAGEMENT':
                    content = doc.get('content', '')
                    found_executives = self.extract_names_from_management(content)
                    executives.update(found_executives)
        
        print(f"📋 Found {len(executives)} executives:")
        for name, role in executives.items():
            print(f"  👤 {name} - {role}")
        
        if not executives:
            print("❌ No executives found in MANAGEMENT entries")
            return
        
        # Step 2: Find their actual dialogue by category
        executive_dialogue_by_category = self.find_executive_dialogue_by_category(data, executives)
        
        total_statements = 0
        for exec_name, categories in executive_dialogue_by_category.items():
            for category, docs in categories.items():
                total_statements += len(docs)
        
        print(f"💬 Found {total_statements} executive dialogue entries across categories")
        
        # Step 3: Organize final data structure
        executives_data = {}
        category_summary = {}
        
        for exec_name, categories in executive_dialogue_by_category.items():
            exec_role = executives.get(exec_name, 'Unknown')
            total_exec_statements = sum(len(docs) for docs in categories.values())
            
            executives_data[exec_name] = {
                'name': exec_name,
                'role': exec_role,
                'total_statements': total_exec_statements,
                'categories': {},
                'category_summary': {}
            }
            
            # Organize by category
            for category_name, documents in categories.items():
                executives_data[exec_name]['categories'][category_name] = {
                    'category_name': category_name,
                    'total_documents': len(documents),
                    'documents': documents
                }
                executives_data[exec_name]['category_summary'][category_name] = len(documents)
                
                # Track overall category stats
                if category_name not in category_summary:
                    category_summary[category_name] = 0
                category_summary[category_name] += len(documents)
        
        # Step 4: Create final structure
        final_data = {
            'company': data['company'],
            'processing_date': data['processing_date'],
            'extraction_type': 'executive_dialogue_by_category',
            'total_executives': len(executives_data),
            'total_executive_statements': total_statements,
            'category_breakdown': category_summary,
            'executives': executives_data,
            'executive_summary': {
                name: {
                    'role': info['role'],
                    'total_statements': info['total_statements'],
                    'top_categories': sorted(info['category_summary'].items(), 
                                           key=lambda x: x[1], reverse=True)[:3]
                }
                for name, info in executives_data.items()
            }
        }
        
        # Step 5: Save results
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved executive dialogue: {output_file}")
        
        # Print detailed summary
        print(f"\n📊 Executive Summary by Category:")
        for name, info in executives_data.items():
            print(f"\n  {name} ({info['role']}): {info['total_statements']} total statements")
            for category, count in sorted(info['category_summary'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    📂 {category}: {count} statements")
        
        print(f"\n📈 Overall Category Breakdown:")
        for category, count in sorted(category_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"  📂 {category}: {count} executive statements")
        
        return final_data

def main():
    """Extract executive dialogue from filtered data"""
    extractor = ExecutiveExtractor()
    
    # Input and output directories
    input_dir = "rag_ready_results/filtered"
    output_dir = "rag_ready_results/executive_only"
    
    # Check input directory
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Get filtered files
    filtered_files = [f for f in os.listdir(input_dir) if f.endswith('_filtered.json')]
    
    if not filtered_files:
        print(f"❌ No filtered files found in {input_dir}")
        return
    
    print(f"🚀 Found {len(filtered_files)} filtered files")
    print("-" * 50)
    
    for file_name in filtered_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, file_name.replace('_filtered.json', '_executives.json'))
        
        try:
            extractor.process_company_data(input_path, output_path)
            print()
        except Exception as e:
            print(f"❌ Error processing {file_name}: {str(e)}")
    
    print("🎉 Executive extraction complete!")
    print(f"📁 Executive files saved in: {output_dir}/")

if __name__ == "__main__":
    main()