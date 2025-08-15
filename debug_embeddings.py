import json
import os

def debug_content_flow():
    """Debug where content is getting corrupted"""
    
    print("🔍 DEBUGGING CONTENT FLOW")
    print("=" * 60)
    
    # Check original executive files
    executive_dir = "rag_ready_results/executive_only"
    embeddings_dir = "rag_ready_results/embeddings"
    
    if not os.path.exists(executive_dir):
        print(f"❌ Executive directory not found: {executive_dir}")
        return
    
    # Load executive file
    exec_files = [f for f in os.listdir(executive_dir) if f.endswith('_executives.json')]
    if not exec_files:
        print("❌ No executive files found")
        return
    
    exec_file = exec_files[0]  # Take first file
    print(f"📂 Analyzing: {exec_file}")
    
    with open(os.path.join(executive_dir, exec_file), 'r', encoding='utf-8') as f:
        exec_data = json.load(f)
    
    print(f"✅ Loaded executive data")
    
    # Sample some content from executives
    sample_count = 0
    for exec_name, exec_info in exec_data.get('executives', {}).items():
        if sample_count >= 3:
            break
            
        print(f"\n👤 EXECUTIVE: {exec_name}")
        print(f"   Role: {exec_info.get('role', 'Unknown')}")
        
        for category, category_data in exec_info.get('categories', {}).items():
            documents = category_data.get('documents', [])
            if documents and sample_count < 3:
                doc = documents[0]  # Take first document
                content = doc.get('content', '')
                
                print(f"\n📂 CATEGORY: {category}")
                print(f"📄 ORIGINAL CONTENT LENGTH: {len(content)} chars")
                print(f"📝 CONTENT PREVIEW:")
                print(f"   Start: '{content[:100]}...'")
                print(f"   End: '...{content[-100:]}'")
                print(f"🔍 FULL CONTENT:")
                print("-" * 40)
                print(content)
                print("-" * 40)
                
                sample_count += 1
                break
        
        if sample_count >= 3:
            break
    
    # Now check embeddings file
    print(f"\n" + "=" * 60)
    print("🔍 CHECKING EMBEDDINGS FILE")
    
    embedding_files = [f for f in os.listdir(embeddings_dir) if f.endswith('_embeddings.json')]
    if not embedding_files:
        print("❌ No embedding files found")
        return
    
    embedding_file = embedding_files[0]
    print(f"📂 Analyzing: {embedding_file}")
    
    with open(os.path.join(embeddings_dir, embedding_file), 'r', encoding='utf-8') as f:
        embed_data = json.load(f)
    
    # Sample embedded content
    documents = embed_data.get('documents', [])
    if documents:
        print(f"📊 Total embedded documents: {len(documents)}")
        
        for i, doc in enumerate(documents[:3]):  # First 3 docs
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            print(f"\n📄 EMBEDDED DOC {i+1}:")
            print(f"   Executive: {metadata.get('executive_name', 'Unknown')}")
            print(f"   Category: {metadata.get('category', 'Unknown')}")
            print(f"   Length: {len(content)} chars")
            print(f"   Quality Score: {metadata.get('quality_score', 'N/A')}")
            print(f"🔍 EMBEDDED CONTENT:")
            print("-" * 40)
            print(content)
            print("-" * 40)
            
            # Check for truncation signs
            if content.endswith('...') or content.startswith('...'):
                print("⚠️  WARNING: Content appears truncated!")
            
            if len(content) < 50:
                print("⚠️  WARNING: Content very short!")
    
    print(f"\n" + "=" * 60)
    print("🎯 ANALYSIS COMPLETE")

def check_embeddings_generator_logic():
    """Check the logic in embeddings generator"""
    
    print("\n🔍 CHECKING EMBEDDINGS GENERATOR LOGIC")
    print("=" * 60)
    
    # Simulate the embeddings generator process
    executive_dir = "rag_ready_results/executive_only"
    exec_files = [f for f in os.listdir(executive_dir) if f.endswith('_executives.json')]
    
    if not exec_files:
        return
    
    with open(os.path.join(executive_dir, exec_files[0]), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🔄 Simulating embeddings generator process...")
    
    for exec_name, exec_data in list(data.get('executives', {}).items())[:1]:  # Just first exec
        print(f"\n👤 Processing: {exec_name}")
        
        for category_name, category_data in list(exec_data.get('categories', {}).items())[:1]:  # Just first category
            documents = category_data.get('documents', [])
            print(f"📂 Category: {category_name} ({len(documents)} docs)")
            
            for i, doc in enumerate(documents[:2]):  # First 2 docs
                content = doc.get('content', '')
                
                print(f"\n📄 Document {i+1}:")
                print(f"   Original ID: {doc.get('id', 'No ID')}")
                print(f"   Original length: {len(content)}")
                
                # Check what quality filter would do
                content_lower = content.lower()
                
                # Simulate quality scoring
                score = 5.0
                
                skip_keywords = [
                    "forward-looking statements", "predictions, projections", 
                    "draw your attention", "thank you, chirag"
                ]
                
                for keyword in skip_keywords:
                    if keyword in content_lower:
                        score -= 2.0
                        print(f"   ⚠️  Found skip keyword: '{keyword}' (score: {score})")
                
                print(f"   📊 Quality score: {score}")
                print(f"   🎯 Would embed: {'Yes' if score >= 4.0 else 'No'}")
                
                if score >= 4.0:
                    print(f"   📝 Content preview: '{content[:150]}...'")

if __name__ == "__main__":
    debug_content_flow()
    check_embeddings_generator_logic()