import json
import re
from typing import Dict, Any
from difflib import SequenceMatcher

def calculate_similarity_score(expected: str, actual: str) -> float:
    """
    Calculate similarity score between expected and actual answers
    Uses a combination of exact matching and semantic similarity
    """
    if not expected or not actual:
        return 0.0
    
    # Clean and normalize text
    expected_clean = clean_text(expected)
    actual_clean = clean_text(actual)
    
    # Calculate sequence similarity
    similarity = SequenceMatcher(None, expected_clean, actual_clean).ratio()
    
    # Calculate word overlap
    expected_words = set(expected_clean.lower().split())
    actual_words = set(actual_clean.lower().split())
    
    if len(expected_words) == 0:
        return 0.0
    
    word_overlap = len(expected_words.intersection(actual_words)) / len(expected_words)
    
    # Combine both metrics (weighted average)
    final_score = (similarity * 0.6) + (word_overlap * 0.4)
    
    return round(final_score, 3)

def clean_text(text: str) -> str:
    """
    Clean and normalize text for comparison
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep alphanumeric and basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text

def parse_json_file(filepath: str) -> Dict[str, Any]:
    """
    Parse JSON file and return data
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error reading JSON file: {str(e)}")

def validate_questions_format(data: Dict[str, Any]) -> bool:
    """
    Validate questions JSON format
    """
    if "questions" not in data:
        return False
    
    if not isinstance(data["questions"], list):
        return False
    
    for question in data["questions"]:
        if not isinstance(question, dict):
            return False
        if "question" not in question:
            return False
    
    return True

def validate_answers_format(data: Dict[str, Any]) -> bool:
    """
    Validate expected answers JSON format
    """
    if "answers" not in data:
        return False
    
    if not isinstance(data["answers"], list):
        return False
    
    for answer in data["answers"]:
        if not isinstance(answer, dict):
            return False
        if "id" not in answer or "expected_answer" not in answer:
            return False
    
    return True