import json
import os
import re
from openai import OpenAI
import hashlib
from datetime import datetime

class SimpleEmbeddingsGenerator:
    def __init__(self, openai_api_key):
        self.client = OpenAI(api_key=openai_api_key)
        
        # Content quality filters
        self.skip_keywords = [
            "forward-looking statements",
            "predictions, projections", 
            "draw your attention",
            "thank you, chirag",
            "good evening and welcome",
            "good morning and welcome",
            "disclaimer before we begin",
            "estimates involve several risks",
            "differ materially from what is expressed",
            "does not undertake any obligation",
            "publicly update any forward-looking",
            "investor relations team",
            "let me draw your attention"
        ]
        
        self.low_value_patterns = [
            r"thank you.*(?:chirag|moderator)",
            r"good (?:evening|morning).*welcome",
            r"i am \w+ from.*investor relations",
            r"let me request \w+ to take over",
            r"would.*like.*request.*to.*over"
        ]
    
    def calculate_content_quality_score(self, content):
        """Score content quality from 1-10 based on business value"""
        content_lower = content.lower()
        score = 5.0  # Base score
        
        # MAJOR PENALTIES for pure administrative content
        admin_phrases = [
            "forward-looking statements", "predictions, projections",
            "draw your attention", "thank you, chirag", "good evening and welcome",
            "disclaimer before we begin", "estimates involve several risks",
            "differ materially from what is expressed", "publicly update any forward-looking",
            "thank you so much for joining", "have a good evening"
        ]
        
        admin_count = sum(1 for phrase in admin_phrases if phrase in content_lower)
        if admin_count >= 2:  # Multiple admin phrases = likely pure disclaimer
            return 1.0  # Very low score
        elif admin_count == 1:
            score -= 3.0  # Single admin phrase penalty
        
        # MAJOR BONUSES for business content indicators
        business_indicators = [
            "revenue", "growth", "margin", "ebitda", "profit", "sales",
            "market", "business", "quarter", "performance", "segment",
            "portfolio", "strategy", "expansion", "investment", "pipeline",
            "competition", "guidance", "outlook", "forecast", "expect"
        ]
        
        business_mentions = sum(1 for keyword in business_indicators if keyword in content_lower)
        if business_mentions >= 5:  # Rich business content
            score += 4.0
        elif business_mentions >= 3:
            score += 2.0
        elif business_mentions >= 1:
            score += 1.0
        
        # MAJOR BONUS for substantial content
        word_count = len(content.split())
        if word_count > 200:  # Substantial statements
            score += 3.0
        elif word_count > 100:
            score += 2.0
        elif word_count > 50:
            score += 1.0
        elif word_count < 20:  # Very short fragments
            score -= 2.0
        
        # BONUS for Q&A content (usually valuable)
        if any(phrase in content_lower for phrase in ["question", "answer", "q:", "a:", "let me"]):
            score += 1.5
        
        # PENALTY for pure closing statements
        closing_phrases = ["thank you for joining", "have a good evening", "any follow on questions"]
        if any(phrase in content_lower for phrase in closing_phrases) and word_count < 100:
            score -= 2.0
        
        return max(1.0, min(10.0, score))  # Clamp between 1-10
    
    def should_embed_content(self, content, min_score=3.5):
        """Determine if content is worth embedding - lowered threshold"""
        score = self.calculate_content_quality_score(content)
        return score >= min_score
    
    def create_embeddings_batch(self, texts, batch_size=100):
        """Generate embeddings in batches for efficiency"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"      🔄 Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch)} documents)")
            
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model="text-embedding-3-small"
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                print(f"      ✅ Batch completed successfully")
                
            except Exception as e:
                print(f"      ❌ Batch failed: {str(e)}")
                # Fallback: try individual embeddings for this batch
                print(f"      🔄 Retrying batch documents individually...")
                for text in batch:
                    try:
                        response = self.client.embeddings.create(
                            input=text,
                            model="text-embedding-3-small"
                        )
                        all_embeddings.append(response.data[0].embedding)
                    except Exception as e2:
                        print(f"      ❌ Individual embedding failed: {str(e2)}")
                        all_embeddings.append(None)
        
        return all_embeddings
    
    def process_executive_file(self, input_file, output_file):
        """Process executive dialogue file and create embeddings"""
        print(f"📂 Processing: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        company = data.get('company', 'Unknown')
        embedded_documents = []
        
        total_docs = 0
        embedded_docs = 0
        skipped_docs = 0
        
        # Process each executive
        for exec_name, exec_data in data.get('executives', {}).items():
            exec_role = exec_data.get('role', 'Unknown')
            print(f"  👤 Processing {exec_name} ({exec_role})")
            
            # Collect all valid documents for this executive
            exec_documents = []
            exec_metadata = []
            
            # Process each category and collect documents
            for category_name, category_data in exec_data.get('categories', {}).items():
                documents = category_data.get('documents', [])
                print(f"    📂 {category_name}: {len(documents)} documents")
                
                for doc in documents:
                    total_docs += 1
                    content = doc.get('content', '')
                    
                    # Quality check
                    quality_score = self.calculate_content_quality_score(content)
                    if not self.should_embed_content(content):
                        skipped_docs += 1
                        continue
                    
                    # Prepare metadata
                    doc_metadata = doc.get('metadata', {})
                    enhanced_metadata = {
                        'document_id': doc.get('id', ''),
                        'company': company,
                        'executive_name': exec_name,
                        'executive_role': exec_role,
                        'category': category_name,
                        'speaker': doc_metadata.get('speaker', ''),
                        'date': doc_metadata.get('date', ''),
                        'quarter': doc_metadata.get('quarter', ''),
                        'fiscal_year': doc_metadata.get('fiscal_year', ''),
                        'source_file': doc_metadata.get('source_file', ''),
                        'content_length': len(content),
                        'word_count': len(content.split()),
                        'quality_score': round(quality_score, 2),
                        'content_type': 'business_insight'
                    }
                    
                    exec_documents.append(content)
                    exec_metadata.append(enhanced_metadata)
            
            # Batch create embeddings for this executive
            if exec_documents:
                print(f"    🚀 Creating embeddings for {len(exec_documents)} high-quality documents...")
                embeddings = self.create_embeddings_batch(exec_documents)
                
                # Create final documents with embeddings
                for i, (content, metadata, embedding) in enumerate(zip(exec_documents, exec_metadata, embeddings)):
                    if embedding is not None:
                        embedded_doc = {
                            'id': metadata['document_id'],
                            'content': content,
                            'embedding': embedding,
                            'metadata': metadata
                        }
                        embedded_documents.append(embedded_doc)
                        embedded_docs += 1
                    else:
                        skipped_docs += 1
        
        # Create final structure
        final_data = {
            'company': company,
            'processing_date': datetime.now().isoformat(),
            'embedding_model': 'text-embedding-3-small',
            'embedding_dimensions': 1536,
            'total_documents_processed': total_docs,
            'documents_embedded': embedded_docs,
            'documents_skipped': skipped_docs,
            'quality_filter_threshold': 4.0,
            'documents': embedded_documents
        }
        
        # Save embeddings file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Processed: {total_docs} total → {embedded_docs} embedded, {skipped_docs} skipped")
        print(f"  📊 Quality threshold filtered out {skipped_docs}/{total_docs} ({skipped_docs/total_docs*100:.1f}%) low-value content")
        print(f"  💾 Saved: {output_file}")
        
        return {
            'total_docs': total_docs,
            'embedded_docs': embedded_docs,
            'skipped_docs': skipped_docs
        }

def main():
    """Generate embeddings for executive dialogue"""
    
    # Set your OpenAI API key
    OPENAI_API_KEY = input("Enter your OpenAI API key: ").strip()
    if not OPENAI_API_KEY:
        print("❌ OpenAI API key is required!")
        return
    
    generator = SimpleEmbeddingsGenerator(OPENAI_API_KEY)
    
    # Input and output directories
    input_dir = "rag_ready_results/executive_only"
    output_dir = "rag_ready_results/embeddings"
    
    # Check input directory
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Get executive files
    exec_files = [f for f in os.listdir(input_dir) if f.endswith('_executives.json')]
    
    if not exec_files:
        print(f"❌ No executive files found in {input_dir}")
        return
    
    print(f"🚀 Found {len(exec_files)} executive files")
    print("-" * 60)
    
    total_embedded = 0
    
    for file_name in exec_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, file_name.replace('_executives.json', '_embeddings.json'))
        
        try:
            result = generator.process_executive_file(input_path, output_path)
            total_embedded += result['embedded_docs']
            print()
        except Exception as e:
            print(f"❌ Error processing {file_name}: {str(e)}")
    
    print("🎉 Embedding generation complete!")
    print(f"📊 Total documents embedded: {total_embedded}")
    print(f"📁 Embeddings saved in: {output_dir}/")
    print("\n💡 Next step: Use these embedding files for RAG implementation!")

if __name__ == "__main__":
    main()