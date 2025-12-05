# questions_manager.py
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from typing import List, Dict, Tuple
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

QUESTIONS_BANK_PATH = Path("data/processed/questions_bank.json")
CACHE_DIR = Path("cache/generated")

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
# --------- Helpers for JSON I/O ---------

def load_question_bank() -> List[Dict]:
    if not QUESTIONS_BANK_PATH.exists():
        return []
    with open(QUESTIONS_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_question_bank(bank: List[Dict]) -> None:
    QUESTIONS_BANK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUESTIONS_BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)


def load_cached_quiz(topic: str, difficulty: str, n_questions: int) -> List[Dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{topic.lower().replace(' ', '_')}_{difficulty.lower()}_{n_questions}.json"
    path = CACHE_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cached_quiz(topic: str, difficulty: str, n_questions: int, questions: List[Dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{topic.lower().replace(' ', '_')}_{difficulty.lower()}_{n_questions}.json"
    path = CACHE_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


# --------- LLM integration (Groq) ---------

def generate_questions_with_groq(
    topic: str,
    difficulty: str,
    n_questions: int
) -> List[Dict]:
    """
    TODO: Implement your Groq API call here.
    This function must return a list of question dicts
    with the same schema as questions in questions_bank.json:

    {
        "topic": str,
        "year": int | None,
        "difficulty": "easy"|"medium"|"hard",
        "question": str,
        "options": {"a": str, "b": str, "c": str, "d": str},
        "correct_answer": "a"|"b"|"c"|"d"
    }
    """
    # Pseudo-code (replace with your actual Groq client call):
    #
    # prompt = f"Generate {n_questions} UPSC-style MCQs on {topic}, difficulty {difficulty}, in JSON..."
    
    prompt = PromptTemplate(
            template=(
                "Generate {n_questions} {difficulty} multiple-choice question about {topic}.\n\n"
                "Return ONLY a JSON object with these exact fields:\n"
                "- 'question': A clear, specific question\n"
                "- 'options': An array of exactly 4 possible answers\n"
                "- 'correct_answer': One of the options that is the correct answer\n\n"
                "Example format:\n"
                '{{\n'
                '    "question": "What is the capital of France?",\n'
                '    "options": ["London", "Berlin", "Paris", "Madrid"],\n'
                '    "correct_answer": "Paris"\n'
                '}}\n\n'
                "Your response:"
            ),
            input_variables=["topic", "difficulty", "n_questions"]
        )
    
    # Render the prompt text
    prompt_text = prompt.format(topic=topic, difficulty=difficulty, n_questions=n_questions)
    
    # Attempt to instantiate and call the Groq client; if not configured or any error occurs,
    # return an empty list so the caller can handle preloaded-only behavior or fallbacks.
    try:
        groq_client = ChatGroq(model="gpt-4o", api_key=groq_api_key)
        response = groq_client.completions.create(messages=[{"role": "user", "content": prompt_text}])
        # Try to extract content from common response shapes
        content = ""
        try:
            content = response.choices[0].message["content"]
        except Exception:
            try:
                content = response.choices[0].text
            except Exception:
                content = ""
        if not content:
            return []
        parsed = json.loads(content)
        # Normalize to a list of question dicts
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return parsed
        return []
    except Exception:
        # If Groq client isn't available or the API call fails, return an empty list
        return []


def select_questions_for_quiz(
    topic: str,
    difficulty: str,
    n_questions: int,
    preloaded_only: bool = False
) -> Tuple[List[Dict], int]:
    """
    Returns:
        questions: list of question dicts
        from_bank_count: how many came from preloaded bank (for debugging / analytics)
    Logic:
      1. Check cache (topic_difficulty_n.json). If exists -> return it.
      2. Else:
         a) Load bank, filter by topic+difficulty.
         b) Use as many as available (up to n).
         c) If still missing and preloaded_only=False -> call Groq for missing.
         d) Append new Groq questions to bank and save.
         e) Save final set (old+new) to cache and return.
    """
    # Step 3: Check cache first
    cached = load_cached_quiz(topic, difficulty, n_questions)
    if cached:
        return cached, len(cached)  # all from bank+cache (no new Groq call)

    # Step A: Bank first
    bank = load_question_bank()
    filtered = [
        q for q in bank
        if q.get("topic", "").lower() == topic.lower()
        and q.get("difficulty", "").lower() == difficulty.lower()
    ]
    from_bank = filtered[:n_questions]

    if len(from_bank) >= n_questions or preloaded_only:
        # Either enough in bank OR user requested no-API mode
        final_questions = from_bank[:n_questions]
        # Cache the exact set for next time
        save_cached_quiz(topic, difficulty, n_questions, final_questions)
        return final_questions, len(final_questions)

    # Step B: Not enough -> need more
    missing = n_questions - len(from_bank)

    # Step B → C: Call Groq only for missing questions
    new_questions = generate_questions_with_groq(topic, difficulty, missing)

    # Ensure new questions have topic/difficulty filled in correctly
    for q in new_questions:
        q.setdefault("topic", topic)
        q.setdefault("difficulty", difficulty.lower())

    # Step C: Append to bank permanently
    bank.extend(new_questions)
    save_question_bank(bank)

    # Build final set: existing + new
    final_questions = from_bank + new_questions

    # Cache this exact set
    save_cached_quiz(topic, difficulty, n_questions, final_questions)

    return final_questions, len(from_bank)
