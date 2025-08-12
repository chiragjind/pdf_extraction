import json
import pandas as pd
import numpy as np
import re
from transformers import pipeline
from tqdm import tqdm
from pathlib import Path
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

class ImprovedFinancialSentimentAnalyzer:
    def __init__(self):
        print("🔄 Loading sentiment models...")
        
        # Load multiple models for ensemble
        try:
            self.finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            print("✅ FinBERT loaded")
        except:
            print("❌ FinBERT failed to load")
            self.finbert = None
            
        try:
            self.financial_roberta = pipeline("sentiment-analysis", 
                                             model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis")
            print("✅ Financial RoBERTa loaded")
        except:
            print("❌ Financial RoBERTa failed to load")
            self.financial_roberta = None
        
        # Management confidence keywords
        self.confidence_keywords = {
            'high_confidence': [
                'confident', 'optimistic', 'strong', 'robust', 'solid', 'excellent', 
                'outstanding', 'promising', 'positive', 'bullish', 'growth', 'expansion',
                'improved', 'better', 'successful', 'achieving', 'exceeded', 'beat',
                'comfortable', 'pleased', 'encouraged', 'momentum', 'accelerating'
            ],
            'low_confidence': [
                'challenging', 'difficult', 'concerned', 'cautious', 'uncertain', 
                'headwinds', 'pressure', 'weak', 'decline', 'volatility', 'risk',
                'disappointed', 'missed', 'below', 'slower', 'postponed', 'delayed',
                'struggle', 'tough', 'worried', 'deterioration', 'weakness'
            ]
        }
        
        # Boilerplate patterns to remove
        self.boilerplate_patterns = [
            r'Scrip Code.*?CIPLA EQ.*?Dear Sirs',
            r'Prepared by:.*?Website.*?com',
            r'Corporate Identity Number.*?PLC\d+',
            r'Regd\. Office.*?Mumbai-\d+',
            r'Phone \+91.*?E-mail.*?com',
            r'Conference Call.*?\d{4}',
            r'\d{6}\s+Scrip Code',
            r'SOCIETE DE LA BOURSE.*?Luxembourg'
        ]
        
    def clean_text(self, text):
        """Clean and preprocess text"""
        if not text or len(text.strip()) < 10:
            return ""
        
        # Remove boilerplate patterns
        cleaned = text
        for pattern in self.boilerplate_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Remove very short fragments
        if len(cleaned) < 20:
            return ""
            
        return cleaned
    
    def extract_speaker_info(self, speaker_text):
        """Extract and clean speaker information"""
        if not speaker_text:
            return "Unknown", "Unknown"
        
        # Clean speaker name
        speaker = re.sub(r'[^\w\s\-\.]', ' ', speaker_text)
        speaker = re.sub(r'\s+', ' ', speaker).strip()
        
        # Determine role
        speaker_lower = speaker.lower()
        
        if any(title in speaker_lower for title in ['ceo', 'chief executive', 'managing director', 'md']):
            role = "CEO/MD"
        elif any(title in speaker_lower for title in ['cfo', 'chief financial']):
            role = "CFO"
        elif any(title in speaker_lower for title in ['coo', 'chief operating']):
            role = "COO"
        elif any(title in speaker_lower for title in ['moderator', 'operator']):
            role = "Moderator"
        elif any(word in speaker_lower for word in ['analyst', 'research', 'investment']):
            role = "Analyst"
        elif any(word in speaker_lower for word in ['management', 'director', 'head', 'president']):
            role = "Management"
        else:
            role = "Other"
            
        return speaker, role
    
    def calculate_management_confidence(self, text, speaker_role):
        """Calculate management confidence score"""
        if not text:
            return 0.5
            
        text_lower = text.lower()
        words = text_lower.split()
        
        if len(words) == 0:
            return 0.5
        
        # Count confidence indicators
        high_count = sum(1 for word in self.confidence_keywords['high_confidence'] 
                        if word in text_lower)
        low_count = sum(1 for word in self.confidence_keywords['low_confidence'] 
                       if word in text_lower)
        
        # Calculate base confidence score
        high_ratio = high_count / len(words)
        low_ratio = low_count / len(words)
        
        base_score = 0.5 + (high_ratio - low_ratio) * 5
        
        # Adjust based on speaker role (management words carry more weight)
        if speaker_role in ["CEO/MD", "CFO", "Management"]:
            weight = 1.2
        elif speaker_role == "Analyst":
            weight = 0.8  # Analyst questions often negative
        else:
            weight = 1.0
            
        confidence_score = base_score * weight
        
        # Normalize to 0-1 range
        return max(0.0, min(1.0, confidence_score))
    
    def get_ensemble_sentiment(self, text):
        """Get sentiment from multiple models"""
        if not text or len(text.strip()) < 10:
            return {
                'ensemble_sentiment': 'neutral',
                'ensemble_score': 0.5,
                'confidence': 0.3
            }
        
        # Truncate if too long
        max_length = 500
        if len(text) > max_length:
            # Try to cut at sentence boundary
            sentences = text.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) < max_length:
                    truncated += sentence + "."
                else:
                    break
            text = truncated if truncated else text[:max_length]
        
        sentiments = []
        scores = []
        
        # FinBERT
        if self.finbert:
            try:
                result = self.finbert(text)[0]
                label = result['label'].lower()
                score = result['score']
                
                if 'positive' in label:
                    sentiments.append(1)
                elif 'negative' in label:
                    sentiments.append(-1)
                else:
                    sentiments.append(0)
                scores.append(score)
            except:
                pass
        
        # Financial RoBERTa
        if self.financial_roberta:
            try:
                result = self.financial_roberta(text)[0]
                label = result['label'].lower()
                score = result['score']
                
                if 'positive' in label:
                    sentiments.append(1)
                elif 'negative' in label:
                    sentiments.append(-1)
                else:
                    sentiments.append(0)
                scores.append(score)
            except:
                pass
        
        # Calculate ensemble
        if sentiments:
            avg_sentiment = np.mean(sentiments)
            avg_confidence = np.mean(scores)
            
            if avg_sentiment > 0.1:
                final_sentiment = 'positive'
            elif avg_sentiment < -0.1:
                final_sentiment = 'negative'
            else:
                final_sentiment = 'neutral'
            
            # Convert to 0-1 scale
            ensemble_score = (avg_sentiment + 1) / 2
            
        else:
            final_sentiment = 'neutral'
            ensemble_score = 0.5
            avg_confidence = 0.3
        
        return {
            'ensemble_sentiment': final_sentiment,
            'ensemble_score': ensemble_score,
            'confidence': avg_confidence
        }
    
    def process_document(self, doc):
        """Process a single document"""
        # Extract and clean content
        content = self.clean_text(doc.get('content', ''))
        if not content:
            return None
        
        # Extract metadata
        metadata = doc.get('metadata', {})
        speaker_raw = metadata.get('speaker', '')
        speaker_role_raw = metadata.get('speaker_role', '')
        
        # Clean speaker info
        speaker, speaker_role = self.extract_speaker_info(speaker_raw)
        
        # Override with existing role if better
        if speaker_role_raw and speaker_role_raw != "Analyst/Other":
            speaker_role = speaker_role_raw
        
        # Get sentiment analysis
        sentiment_result = self.get_ensemble_sentiment(content)
        
        # Calculate management confidence
        confidence = self.calculate_management_confidence(content, speaker_role)
        
        # Parse date properly
        date_str = metadata.get('date', '')
        try:
            date_parsed = pd.to_datetime(date_str)
        except:
            date_parsed = None
        
        return {
            'company': metadata.get('company', ''),
            'category': 'Unknown',  # Will be filled by caller
            'speaker': speaker,
            'speaker_role': speaker_role,
            'date': date_parsed,
            'quarter': metadata.get('quarter', ''),
            'fiscal_year': metadata.get('fiscal_year', ''),
            'source_file': metadata.get('source_file', ''),
            'content': content,
            'content_length': len(content),
            'word_count': len(content.split()),
            'sentiment': sentiment_result['ensemble_sentiment'],
            'sentiment_score': sentiment_result['ensemble_score'],
            'sentiment_confidence': sentiment_result['confidence'],
            'management_confidence': confidence
        }
    
    def analyze_company_data(self, json_file_path):
        """Main analysis function"""
        print(f"\n📊 Processing {json_file_path}")
        
        # Load data
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        company = data.get("company", "Unknown")
        categories = data.get("categories", {})
        
        print(f"🏢 Company: {company}")
        print(f"📁 Categories found: {len(categories)}")
        
        # Process all documents
        all_results = []
        total_docs = sum(len(cat_data.get("documents", [])) for cat_data in categories.values())
        
        print(f"📄 Total documents to process: {total_docs}")
        
        with tqdm(total=total_docs, desc="Processing documents") as pbar:
            for category_name, category_data in categories.items():
                documents = category_data.get("documents", [])
                
                for doc in documents:
                    result = self.process_document(doc)
                    if result:
                        result['category'] = category_name
                        all_results.append(result)
                    pbar.update(1)
        
        # Create DataFrame
        df = pd.DataFrame(all_results)
        
        if df.empty:
            print("❌ No valid data processed!")
            return None, None
        
        # Additional cleaning
        df = df.dropna(subset=['date', 'content'])
        df = df[df['content_length'] >= 20]  # Filter very short content
        
        # Add derived columns
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['year_quarter'] = df['date'].dt.to_period('Q').astype(str)  # Convert to string for JSON
        
        print(f"✅ Successfully processed {len(df)} documents")
        print(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"👥 Speakers: {df['speaker_role'].value_counts().to_dict()}")
        print(f"📊 Sentiment distribution: {df['sentiment'].value_counts().to_dict()}")
        
        return df, company
    
    def calculate_summary_metrics(self, df):
        """Calculate summary metrics - FIXED for JSON serialization"""
        if df.empty:
            return {}
        
        summary = {
            'overall_metrics': {
                'total_documents': len(df),
                'avg_sentiment_score': float(df['sentiment_score'].mean()),
                'avg_management_confidence': float(df['management_confidence'].mean()),
                'sentiment_distribution': df['sentiment'].value_counts().to_dict(),
                'date_range': {
                    'start': df['date'].min().isoformat(),
                    'end': df['date'].max().isoformat()
                }
            },
            'by_speaker_role': {},
            'by_category': {},
            'by_quarter': {}
        }
        
        # By speaker role
        for role in df['speaker_role'].unique():
            role_data = df[df['speaker_role'] == role]
            summary['by_speaker_role'][role] = {
                'count': len(role_data),
                'avg_sentiment': float(role_data['sentiment_score'].mean()),
                'avg_confidence': float(role_data['management_confidence'].mean()),
                'sentiment_dist': role_data['sentiment'].value_counts().to_dict()
            }
        
        # By category
        for category in df['category'].unique():
            cat_data = df[df['category'] == category]
            summary['by_category'][category] = {
                'count': len(cat_data),
                'avg_sentiment': float(cat_data['sentiment_score'].mean()),
                'avg_confidence': float(cat_data['management_confidence'].mean())
            }
        
        # By quarter - FIXED: Convert to string keys
        quarterly = df.groupby('year_quarter').agg({
            'sentiment_score': 'mean',
            'management_confidence': 'mean',
            'sentiment': lambda x: (x == 'positive').sum() / len(x)
        }).round(3)
        
        # Convert to dictionary with string keys
        summary['by_quarter'] = {str(k): v for k, v in quarterly.to_dict('index').items()}
        
        return summary

def main():
    analyzer = ImprovedFinancialSentimentAnalyzer()
    
    # Process companies
    companies = ["cipla", "lupin"]
    
    for company in companies:
        json_file = f"rag_ready_results/complete/{company}_complete.json"
        
        if not Path(json_file).exists():
            print(f"❌ File not found: {json_file}")
            continue
        
        # Analyze
        df, company_name = analyzer.analyze_company_data(json_file)
        
        if df is not None:
            # Calculate metrics
            metrics = analyzer.calculate_summary_metrics(df)
            
            # Save detailed results
            output_dir = Path("output/improved_sentiment")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save CSV
            csv_path = output_dir / f"{company}_detailed_sentiment.csv"
            df.to_csv(csv_path, index=False)
            
            # Save metrics JSON - NOW WORKS!
            json_path = output_dir / f"{company}_sentiment_metrics.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n📊 {company.upper()} RESULTS:")
            print(f"  📄 Documents processed: {len(df)}")
            print(f"  📈 Average sentiment score: {metrics['overall_metrics']['avg_sentiment_score']:.3f}")
            print(f"  🎯 Management confidence: {metrics['overall_metrics']['avg_management_confidence']:.3f}")
            print(f"  💾 Saved to: {csv_path}")
            print(f"  📋 Metrics saved to: {json_path}")
    
    print("\n🎉 Analysis complete!")

if __name__ == "__main__":
    main()