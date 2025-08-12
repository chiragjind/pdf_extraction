import json
import pandas as pd
from transformers import pipeline
from tqdm import tqdm
from pathlib import Path

# ==== Load JSON ====
with open("rag_ready_results/complete/cipla_complete.json", "r", encoding="utf-8") as f:
    data = json.load(f)

company = data.get("company", "Unknown")
categories = data.get("categories", {})

# ==== Flatten into rows ====
rows = []
for category_name, cat_data in categories.items():
    for doc in cat_data.get("documents", []):  # <-- FIXED HERE
        date_val = doc.get("metadata", {}).get("date", None)
        rows.append({
            "company": company,
            "category": category_name,
            "date": date_val,
            "content": doc.get("content", "")
        })

df = pd.DataFrame(rows)

# ==== Clean Dates ====
df = df.dropna(subset=["date"])
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
df["quarter"] = df["date"].dt.to_period("Q")

# ==== Load FinBERT ====
sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")

# ==== Apply Sentiment ====
labels, scores = [], []
for text in tqdm(df["content"], desc="Running sentiment analysis"):
    result = sentiment_pipeline(text[:512])[0]  # truncate to avoid long input issues
    labels.append(result["label"])
    scores.append(result["score"])

df["sentiment"] = labels
df["sentiment_score"] = scores

# ==== Save ====
output_path = Path("output/sentiment_results.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print(f"✅ Saved sentiment results to {output_path}")
