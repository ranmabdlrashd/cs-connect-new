import os
import logging
import json
import collections
import time
import re
from typing import List, Dict, Any, Optional
from groq import Groq
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# In-memory cache for last 10 queries
chat_cache = collections.OrderedDict()
MAX_CACHE_SIZE = 10

BASE_DIR = "static/uploads/notes"

def get_safe_pdf_url(filename: str) -> Optional[str]:
    """
    Sanitizes and validates filename to prevent path traversal and unauthorized access.
    Returns a safe relative URL or None.
    """
    if not filename:
        return None
        
    # 1. Sanitize filename (extract only the basename)
    safe_name = os.path.basename(filename)
    
    # 2. Validate filename
    if not safe_name or ".." in safe_name:
        logging.warning("Blocked invalid file path attempt: %s", filename)
        return None
        
    # 3. Secure path construction
    safe_path = os.path.join(BASE_DIR, safe_name)
    
    # 4. Prevent path escape (critical check)
    full_path = os.path.abspath(safe_path)
    base_abs_dir = os.path.abspath(BASE_DIR)
    
    if not full_path.startswith(base_abs_dir):
        logging.warning("Path traversal attempt detected: %s", filename)
        return None
        
    # 5. Check if file exists
    if not os.path.exists(full_path):
        return None
        
    # 6. Generate safe URL
    return f"/static/uploads/notes/{safe_name}"

def extract_keywords(user_input: str) -> List[str]:
    """
    Pure Python keyword extraction (no LLM).
    """
    stop_words = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'for', 'and', 'or', 'in', 'on', 'at', 
        'about', 'how', 'what', 'where', 'when', 'why', 'who', 'tell', 'me', 'please', 
        'give', 'show', 'can', 'you', 'find', 'search', 'get', 'help'
    }
    # Clean input
    cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in user_input.lower())
    words = cleaned.split()
    
    # Filter keywords
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return list(set(keywords))

def fetch_relevant_data(keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Executes a single optimized SQL query to fetch relevant data across all categories.
    Implements ranking, limiting (5), and parameterization to prevent SQL injection.
    """
    if not keywords:
        return []

    # Build patterns for ILIKE ANY
    patterns = [f"%{kw}%" for kw in keywords]
    first_keyword_pattern = f"%{keywords[0]}%"

    conn = get_db_connection()
    if not conn:
        return []

    results = []
    try:
        with conn.cursor() as cur:
            # Combined query using UNION ALL for a single database hit
            # Unifies disparate table structures into a clean, structured format
            query = """
                SELECT * FROM (
                    SELECT 'FACULTY' as category, name as title, 
                           'Designation: ' || designation || ' | Research: ' || research as details,
                           email as extra
                    FROM faculty 
                    WHERE name ILIKE ANY(%s) OR research ILIKE ANY(%s) OR designation ILIKE ANY(%s)
                    
                    UNION ALL
                    
                    SELECT 'STUDY MATERIAL' as category, document_name as title, 
                           content as details,
                           NULL as extra
                    FROM document_chunks 
                    WHERE document_name ILIKE ANY(%s) OR content ILIKE ANY(%s)
                    
                    UNION ALL
                    
                    SELECT 'LIBRARY' as category, title as title, 
                           'Author: ' || author || ' | Category: ' || category as details,
                           availability::text as extra
                    FROM books 
                    WHERE title ILIKE ANY(%s) OR author ILIKE ANY(%s)
                    
                    UNION ALL
                    
                    SELECT 'ALUMNI' as category, name as title, 
                           'Placed at: ' || company as details,
                           package as extra
                    FROM alumni 
                    WHERE name ILIKE ANY(%s) OR company ILIKE ANY(%s)
                    
                    UNION ALL
                    
                    SELECT 'SUBJECT' as category, full_name as title, 
                           'Code: ' || code as details,
                           faculty_name as extra
                    FROM timetable_subjects 
                    WHERE full_name ILIKE ANY(%s) OR code ILIKE ANY(%s)
                    
                    UNION ALL
                    
                    SELECT 'INFO' as category, title as title, 
                           content as details,
                           NULL as extra
                    FROM website_content 
                    WHERE title ILIKE ANY(%s) OR content ILIKE ANY(%s)
                ) as search_results
                ORDER BY 
                    CASE 
                        WHEN title ILIKE %s THEN 1 
                        ELSE 2 
                    END
                LIMIT 5
            """
            
            # Param mapping for each table's ILIKE ANY columns + the ranking pattern
            params = [
                patterns, patterns, patterns, # Faculty
                patterns, patterns,           # Study Material
                patterns, patterns,           # Library
                patterns, patterns,           # Alumni
                patterns, patterns,           # Subject
                patterns, patterns,           # Info
                first_keyword_pattern         # Rank priority for first keyword
            ]
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            # Convert rows to clean structured dictionaries
            for row in rows:
                results.append({
                    "category": row[0],
                    "title": row[1],
                    "details": row[2],
                    "extra": row[3]
                })
                
    except Exception as e:
        logger.exception("Database Search Error")
    finally:
        conn.close()

    # Optional Fallback: broader search logic can be implemented here if results are empty
    # For now, ILIKE ANY with multiple patterns is already broad enough for context retrieval.
    return results

def fetch_db_context(keywords: List[str]) -> str:
    """
    Fetches targeted context using optimized search and formats it for LLM consumption.
    """
    results = fetch_relevant_data(keywords)
    if not results:
        return ""

    context_parts = []
    for r in results:
        cat = r['category']
        title = r['title']
        details = r['details']
        extra = r['extra']
        
        if cat == 'FACULTY':
            context_parts.append(f"FACULTY: {title}, {details}, Contact: {extra}")
        elif cat == 'STUDY MATERIAL':
            pdf_url = get_safe_pdf_url(title)
            if pdf_url:
                context_parts.append(f"STUDY MATERIAL (PDF): {title} | Preview: {details[:250]} | URL: {pdf_url}")
            else:
                context_parts.append(f"STUDY MATERIAL: {title} | Preview: {details[:250]} | File not available")
        elif cat == 'LIBRARY':
            context_parts.append(f"LIBRARY BOOK: {title} | {details} (Availability: {extra})")
        elif cat == 'ALUMNI':
            context_parts.append(f"ALUMNI: {title} | {details} ({extra})")
        elif cat == 'SUBJECT':
            context_parts.append(f"SUBJECT: {title} | {details} - Faculty: {extra}")
        elif cat == 'INFO':
            context_parts.append(f"INFO: {title} - {details[:300]}")

    # Deduplicate and format final context string
    unique_context = list(dict.fromkeys(context_parts))
    return "\n".join(unique_context)

def safe_parse_json(text: str) -> Dict[str, Any]:
    """
    Safely parses JSON from LLM output, extracting it from markdown blocks if necessary.
    Provides a fallback if parsing fails.
    """
    fallback = {
        "type": "text",
        "message": "I'm sorry, I encountered an error processing that request.",
        "file_url": None
    }
    
    if not text:
        return fallback

    try:
        # 1. Clean whitespace and unexpected characters
        cleaned_text = text.strip()
        
        # 2. Try to find JSON in markdown code blocks
        json_match = re.search(r"```json\s*(.*?)\s*```", cleaned_text, re.DOTALL)
        if json_match:
            cleaned_text = json_match.group(1)
        else:
            # 3. Try to find the first '{' and last '}'
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}')
            if start != -1 and end != -1:
                cleaned_text = cleaned_text[start:end+1]

        # 4. Final parse
        return json.loads(cleaned_text)
    except Exception:
        logger.warning("Failed to parse LLM JSON output: %s", text[:200])
        # Try to return the raw text if it looks like a simple message
        if "{" not in text:
             return {"type": "text", "message": text.strip(), "file_url": None}
        return fallback

def generate_chatbot_response(user_input: str, chat_history: List[dict]) -> Dict[str, Any]:
    """
    Core function: Returns a structured dictionary based on user input and DB context.
    """
    # 1. Check Cache
    if user_input in chat_cache:
        chat_cache.move_to_end(user_input)
        return chat_cache[user_input]

    # 2. Extract Keywords & Context
    keywords = extract_keywords(user_input)
    context = fetch_db_context(keywords)

    # 3. Build System Prompt (STRICT JSON ONLY)
    system_prompt = (
        "You are the 'CS Connect Assistant', a helpful and concise college chatbot for the CSE department.\n\n"
        "CORE RULES:\n"
        "1. Always respond in valid JSON format ONLY.\n"
        "2. Do NOT return plain text outside the JSON structure.\n"
        "3. Use the following schema:\n"
        "   {\n"
        "     \"type\": \"text\" | \"notes_button\",\n"
        "     \"message\": \"string content\",\n"
        "     \"file_url\": \"relative URL or null\"\n"
        "   }\n"
        "4. NOTES/STUDY MATERIAL: If a relevant PDF exists in the context below, set \"type\": \"notes_button\" and provide the \"file_url\". Otherwise, use \"type\": \"text\".\n"
        "5. If no data is found, return:\n"
        "   {\"type\": \"text\", \"message\": \"I couldn't find relevant information.\", \"file_url\": null}\n"
        "6. Use ONLY the provided database context. NEVER hallucinate.\n\n"
        "DATABASE CONTEXT:\n"
        f"{context if context else 'No relevant data found in database.'}"
    )

    # 5. Build Messages
    messages = [{"role": "system", "content": system_prompt}]
    # Add last few turns of history for context
    for msg in chat_history[-5:]:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_input})

    # 6. Call LLM Once with Failure Handling & Timeout (3 Retries)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info("Calling Groq API (Attempt %d/%d) for user_input='%s'", attempt + 1, max_retries, user_input[:50])
            completion = client.chat.completions.create(
                messages=messages,
                model=MODEL,
                temperature=0.2, # Lower temperature for strictly formatted JSON
                max_tokens=500,
                timeout=20.0 
            )
            raw_response = completion.choices[0].message.content
            structured_response = safe_parse_json(raw_response)

            # 7. Update Cache
            chat_cache[user_input] = structured_response
            if len(chat_cache) > MAX_CACHE_SIZE:
                chat_cache.popitem(last=False)

            return structured_response

        except Exception:
            logger.warning("Retry %d failed for Groq API call", attempt + 1)
            if attempt == max_retries - 1:
                logger.exception("Persistent failure calling Groq API")
                return {
                    "type": "text", 
                    "message": "AI service is temporarily unavailable. Please try again later.",
                    "file_url": None
                }
            time.sleep(1)

def generate_response(messages: List[dict], is_logged_in: bool = False) -> Dict[str, Any]:
    """
    Wrapper for compatibility with app.py. Returns a structured JSON-able dict.
    """
    if not messages:
        return {"type": "text", "message": "I didn't receive any message.", "file_url": None}
        
    try:
        # If passed a list of messages, extract the latest user input
        user_input = messages[-1]['content']
        # Convert internal history to match what LLM expects if needed,
        # but here we just pass the history as is.
        # Ensure we only pass text content for history, even if it was previously JSON.
        sanitized_history = []
        for msg in messages[:-1]:
            content = msg.get('content', '')
            if isinstance(content, dict):
                content = content.get('message', '')
            sanitized_history.append({"role": msg.get('role', 'user'), "content": content})
            
        return generate_chatbot_response(user_input, sanitized_history)
    except Exception:
        logger.exception("Unexpected error in generate_response wrapper")
        return {
            "type": "text", 
            "message": "I encountered an error processing your request.",
            "file_url": None
        }

if __name__ == "__main__":
    logger.info("Running LLM Engine test...")
    test_msgs = [{"role": "user", "content": "What are the department stats?"}]
    logger.info("Response: %s", generate_response(test_msgs, False))

