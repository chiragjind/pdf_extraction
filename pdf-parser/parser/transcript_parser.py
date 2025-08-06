# pdf-parser/parser/transcript_parser.py

import re

def clean_dialogue_text(text):
    """Clean text for proper JSON formatting"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove any control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Replace multiple newlines with single space
    text = re.sub(r'\n+', ' ', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text

def parse_transcript(text):
    """Parse transcript into speakers and dialogue"""
    speakers = set()
    dialogue = []
    current_speaker = None
    current_text = []
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for Moderator
        if line.startswith('Moderator:'):
            if current_speaker and current_text:
                combined_text = clean_dialogue_text(' '.join(current_text))
                if combined_text:
                    dialogue.append({
                        "speaker": current_speaker,
                        "text": combined_text
                    })
            current_speaker = "Moderator"
            speakers.add("Moderator")
            current_text = [line[10:].strip()]
            continue
        
        # Check for Speaker Name:
        match = re.match(r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s*:\s*(.*)$', line)
        if match:
            name = match.group(1).strip()
            # Validate speaker name
            if len(name) > 2 and name.lower() not in ['page', 'question', 'answer', 'operator', 'company']:
                if current_speaker and current_text:
                    combined_text = clean_dialogue_text(' '.join(current_text))
                    if combined_text:
                        dialogue.append({
                            "speaker": current_speaker,
                            "text": combined_text
                        })
                current_speaker = name
                speakers.add(name)
                current_text = [match.group(2).strip()]
                continue
        
        # Add to current speaker's text
        if current_speaker:
            current_text.append(line)
    
    # Add last speaker
    if current_speaker and current_text:
        combined_text = clean_dialogue_text(' '.join(current_text))
        if combined_text:
            dialogue.append({
                "speaker": current_speaker,
                "text": combined_text
            })
    
    return sorted(list(speakers)), dialogue