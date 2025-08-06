import re

def clean_text(text):
    """Clean extracted text"""
    # Fix character spacing (''' issue)
    text = re.sub(r"'''", "", text)
    text = re.sub(r"'", "", text)
    
    # Fix quotes and special chars
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace('–', '-').replace('—', '-')
    
    # Clean whitespace
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove page numbers
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    
    return text.strip()