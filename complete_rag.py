import json
import numpy as np
from openai import OpenAI
import os
from typing import List, Dict, Tuple
from datetime import datetime

class CompleteRAGSystem:
    def __init__(self, openai_api_key):
        self.client = OpenAI(api_key=openai_api_key)
        self.companies_data = {}
        self.load_embeddings()
    
    def load_embeddings(self):
        """Load all embedding files"""
        embeddings_dir = "rag_ready_results/embeddings"
        
        if not os.path.exists(embeddings_dir):
            print(f"❌ Embeddings directory not found: {embeddings_dir}")
            return
        
        # Load all embedding files
        for filename in os.listdir(embeddings_dir):
            if filename.endswith('_embeddings.json'):
                company_name = filename.replace('_embeddings.json', '').upper()
                file_path = os.path.join(embeddings_dir, filename)
                
                print(f"📂 Loading {company_name} embeddings...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.companies_data[company_name] = {
                    'documents': data['documents'],
                    'total_docs': len(data['documents'])
                }
                
                print(f"✅ Loaded {len(data['documents'])} documents for {company_name}")
        
        total_docs = sum(company['total_docs'] for company in self.companies_data.values())
        print(f"\n🎯 Ready! Loaded {len(self.companies_data)} companies, {total_docs} total documents")
    
    def create_question_embedding(self, question: str):
        """Convert question to embedding"""
        try:
            response = self.client.embeddings.create(
                input=question,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error creating question embedding: {str(e)}")
            return None
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def calculate_weighted_score(self, similarity: float, date_str: str, content_quality: float = None):
        """Calculate final score combining similarity, recency, and quality"""
        try:
            # Parse date
            doc_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            current_date = datetime.now()
            
            # Calculate days ago
            days_ago = (current_date - doc_date).days
            
            # Recency weight (more recent = higher weight)
            if days_ago <= 90:  # Last 3 months
                recency_weight = 1.0
            elif days_ago <= 365:  # Last year
                recency_weight = 0.8
            elif days_ago <= 730:  # Last 2 years
                recency_weight = 0.6
            else:  # Older than 2 years
                recency_weight = 0.4
            
            # Quality weight (from embeddings generation)
            quality_weight = (content_quality or 5.0) / 10.0  # Normalize to 0-1
            
            # Combined weighted score
            # 70% similarity + 20% recency + 10% quality
            weighted_score = (similarity * 0.7) + (recency_weight * 0.2) + (quality_weight * 0.1)
            
            return weighted_score, recency_weight, days_ago
            
        except Exception as e:
            # Fallback to just similarity if date parsing fails
            return similarity, 1.0, 0
    
    def search_documents(self, question: str, top_k: int = 5, company_filter: str = None):
        """Search for most relevant documents"""
        print(f"🔍 Searching for: '{question}'")
        
        # Create question embedding
        question_embedding = self.create_question_embedding(question)
        if question_embedding is None:
            return []
        
        all_results = []
        
        # Search through all companies (or filtered company)
        companies_to_search = [company_filter.upper()] if company_filter else self.companies_data.keys()
        
        for company_name in companies_to_search:
            if company_name not in self.companies_data:
                continue
                
            company_data = self.companies_data[company_name]
            
            for doc in company_data['documents']:
                doc_embedding = doc.get('embedding')
                if doc_embedding is None:
                    continue
                
                # Calculate similarity
                similarity = self.cosine_similarity(question_embedding, doc_embedding)
                
                # Get content quality score
                quality_score = doc['metadata'].get('quality_score', 5.0)
                
                # Calculate weighted score (similarity + recency + quality)
                weighted_score, recency_weight, days_ago = self.calculate_weighted_score(
                    similarity, 
                    doc['metadata'].get('date', ''), 
                    quality_score
                )
                
                result = {
                    'company': company_name,
                    'similarity': similarity,
                    'weighted_score': weighted_score,
                    'recency_weight': recency_weight,
                    'days_ago': days_ago,
                    'quality_score': quality_score,
                    'content': doc['content'],
                    'metadata': doc['metadata']
                }
                
                all_results.append(result)
        
        # Sort by weighted score (highest first)
        all_results.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        return all_results[:top_k]
    
    def format_search_results(self, results: List[Dict]):
        """Format search results for display"""
        if not results:
            return "No relevant documents found."
        
        formatted = []
        
        for i, result in enumerate(results, 1):
            company = result['company']
            similarity = result['similarity']
            weighted_score = result['weighted_score']
            days_ago = result['days_ago']
            content = result['content']
            metadata = result['metadata']
            
            # Extract key metadata
            executive = metadata.get('executive_name', metadata.get('speaker', 'Unknown'))
            role = metadata.get('executive_role', 'Unknown Role')
            category = metadata.get('category', 'Unknown Category')
            date = metadata.get('date', '')[:10]  # Just date part
            quarter = metadata.get('quarter', '')
            fiscal_year = metadata.get('fiscal_year', '')
            
            # Create time context
            if days_ago < 30:
                time_context = "🟢 Recent"
            elif days_ago < 365:
                time_context = "🟡 This Year"
            elif days_ago < 730:
                time_context = "🟠 Last Year"
            else:
                time_context = "🔴 Older"
            
            formatted_result = f"""
🏢 Result {i} - {company} (Score: {weighted_score:.3f}, Similarity: {similarity:.3f})
👤 {executive} ({role})
📂 Category: {category}
📅 {time_context} {date} {quarter} {fiscal_year} ({days_ago} days ago)
💬 Content: {content[:200]}{'...' if len(content) > 200 else ''}
{'-' * 80}"""
            
            formatted.append(formatted_result)
        
        return '\n'.join(formatted)
    
    def generate_comprehensive_answer(self, question: str, search_results: List[Dict]):
        """Generate comprehensive business analysis using OpenAI"""
        if not search_results:
            return "I couldn't find relevant information to answer your question."
        
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # Top 5 results
            company = result['company']
            exec_name = result['metadata'].get('executive_name', 'Unknown')
            role = result['metadata'].get('executive_role', 'Unknown')
            category = result['metadata'].get('category', 'Unknown')
            date = result['metadata'].get('date', '')[:10]
            quarter = result['metadata'].get('quarter', '')
            content = result['content']
            
            context_part = f"""
Source {i}: {company} - {exec_name} ({role})
Category: {category} | Date: {date} {quarter}
Content: {content}
---"""
            context_parts.append(context_part)
        
        context = '\n'.join(context_parts)
        
        # Create comprehensive business analysis prompt
        prompt = f"""You are a senior business analyst with 15+ years of experience analyzing public companies across industries. Based on the provided earnings call transcripts, deliver a comprehensive business intelligence report.

User Question: {question}

Recent Earnings Call Context:
{context}

COMPREHENSIVE ANALYSIS FRAMEWORK:

📊 FINANCIAL HEALTH & TRENDS:
- Revenue growth patterns, margin trajectories, profitability trends
- Quarter-over-quarter and year-over-year performance analysis
- Cash flow generation, debt levels, return metrics

🏭 OPERATIONAL PERFORMANCE:
- Business capacity utilization, operational efficiency
- Supply chain resilience, inventory management
- Cost optimization initiatives, productivity improvements

🎯 PRODUCT/SERVICE PORTFOLIO:
- New product/service launches and market reception
- Innovation pipeline and development progress
- Portfolio mix and performance by segment

🌍 MARKET POSITIONING & EXPANSION:
- Geographic revenue mix and market presence
- Market share evolution, competitive positioning
- Pricing dynamics and market trends

⚖️ REGULATORY & COMPLIANCE:
- Regulatory environment and compliance status
- Industry-specific approvals and certifications
- Quality initiatives and governance

💼 MANAGEMENT STRATEGY & EXECUTION:
- Strategic priorities and execution progress
- Capital allocation decisions, M&A activities
- Leadership stability and organizational changes

⚠️ RISK ASSESSMENT:
- Industry risks, competitive threats
- Economic impacts, operational vulnerabilities
- Market pressures and business challenges

🔮 FORWARD-LOOKING INSIGHTS:
- Management guidance and confidence levels
- Growth drivers and investment priorities
- Market outlook and strategic positioning

RESPONSE STRUCTURE:
1. **Executive Summary** (2-3 key takeaways)
2. **Detailed Analysis** (organize by relevant categories above)
3. **Latest Trends** (highlight most recent developments)
4. **Management Stability** (leadership confidence, strategic consistency)
5. **Comparative Context** (if multiple companies, clear comparisons)
6. **Source Attribution** (cite specific executives and dates)

CRITICAL REQUIREMENTS:
- Prioritize recent information (highlight latest quarters)
- Distinguish between management statements vs analyst questions
- Flag any concerning trends or positive momentum
- Use specific numbers, percentages, and metrics when available
- Maintain objectivity while highlighting management confidence/concerns

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                messages=[
                    {"role": "system", "content": "You are a senior business analyst expert in earnings call analysis. Provide detailed, accurate, and well-structured responses based on the provided earnings call transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1  # Low temperature for factual responses
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def chat_with_rag(self, question: str, company_filter: str = None):
        """Complete RAG workflow: search + generate comprehensive answer"""
        print(f"🔍 Searching for: '{question}'")
        
        # Search for relevant documents
        search_results = self.search_documents(question, top_k=5, company_filter=company_filter)
        
        if not search_results:
            return "I couldn't find relevant information to answer your question."
        
        print(f"✅ Found {len(search_results)} relevant sources")
        print("🤖 Generating comprehensive analysis...\n")
        
        # Generate comprehensive answer
        answer = self.generate_comprehensive_answer(question, search_results)
        
        return answer, search_results

def main():
    """Interactive RAG chatbot interface"""
    print("🚀 Complete RAG Business Intelligence System")
    print("=" * 60)
    
    # Get OpenAI API key
    api_key = input("Enter your OpenAI API key: ").strip()
    if not api_key:
        print("❌ API key required!")
        return
    
    # Initialize RAG system
    rag = CompleteRAGSystem(api_key)
    
    if not rag.companies_data:
        print("❌ No embedding data loaded!")
        return
    
    print("\n🎯 RAG Business Intelligence Chatbot Ready!")
    print("\nExample questions:")
    print("- 'What is CIPLA's overall business performance?'")
    print("- 'Compare CIPLA and LUPIN strategic positioning'") 
    print("- 'Latest trends in management strategy'")
    print("- 'Risk assessment for both companies'")
    print("- 'Financial health and operational performance'")
    print("\nCommands:")
    print("- Type 'quit' to exit")
    print("- Add 'company:CIPLA' to focus on CIPLA only")
    print("- Add 'company:LUPIN' to focus on LUPIN only")
    print("- Type 'sources' before a question to see detailed sources")
    
    show_sources = False
    
    while True:
        print("\n" + "=" * 60)
        question = input("❓ Your business question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if question.lower() == 'sources':
            show_sources = True
            print("✅ Will show detailed sources for the next question")
            continue
            
        if not question:
            continue
        
        # Check for company filter
        company_filter = None
        if 'company:' in question.lower():
            parts = question.split('company:')
            if len(parts) == 2:
                question = parts[0].strip()
                company_filter = parts[1].strip()
        
        # Get comprehensive AI response
        try:
            result = rag.chat_with_rag(question, company_filter=company_filter)
            
            if isinstance(result, tuple):
                answer, sources = result
                
                # Display comprehensive AI answer
                print("🤖 Comprehensive Business Analysis:")
                print("=" * 60)
                print(answer)
                
                # Optionally show detailed sources
                if show_sources:
                    print("\n📚 Detailed Sources:")
                    print("=" * 60)
                    print(rag.format_search_results(sources))
                    show_sources = False
                else:
                    print(f"\n💡 Tip: Type 'sources' before your next question to see detailed source information")
            else:
                print("🤖 Response:", result)
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()