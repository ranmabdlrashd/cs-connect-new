import os
import json
from typing import List
from groq import Groq
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client (Llama 3.3 70B)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def analyze_intent(user_query: str, chat_history: List[dict]) -> dict:
    """
    Uses Claude to determine the subject of the query and extract keywords.
    """
    history_str = ""
    for msg in chat_history[-3:]: # Only look at last 3 for intent
        role = "User" if msg['role'] == 'user' else "AI"
        history_str += f"{role}: {msg['content']}\n"

    system_prompt = (
        "You are a Search Intent Analyzer for a college department portal.\n"
        "Your goal is to determine EXACTLY what the user wants to search for, considering conversation history.\n"
        "Available Categories: ['faculty', 'library', 'academics', 'placements', 'events', 'general']\n\n"
        "Return ONLY a JSON object with this structure (no Markdown wrap):\n"
        "{\n"
        "  \"intent\": \"faculty|library|academics|placements|events|general\",\n"
        "  \"subject\": \"the actual noun they are talking about\",\n"
        "  \"keywords\": [\"list\", \"of\", \"keywords\"]\n"
        "}"
    )

    user_prompt = f"CONVERSATION HISTORY:\n{history_str}\n\nCURRENT QUERY: {user_query}"

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            model=MODEL,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Intent Analysis Error: {e}")
        return {"intent": "general", "subject": user_query, "keywords": [user_query]}

def get_context_by_intent(analysis: dict) -> str:
    """
    Fetches targeted context based on the analyzed intent and subject.
    """
    intent = analysis.get("intent", "general")
    subject = analysis.get("subject", "")
    keywords = analysis.get("keywords", [])
    
    if not keywords:
        keywords = [subject]

    conn = get_db_connection()
    if not conn:
        return "Critical Error: Could not connect to database."

    context_parts: List[str] = []
    
    try:
        with conn.cursor() as cur:
            for kw in keywords[:3]:
                search_term = f"%{kw}%"
                
                if intent == 'faculty':
                    cur.execute("SELECT name, designation, qualification, research, email FROM faculty WHERE name ILIKE %s OR designation ILIKE %s OR research ILIKE %s", (search_term, search_term, search_term))
                    for f in cur.fetchall():
                        context_parts.append(f"FACULTY: {f[0]}, {f[1]}, Qual: {f[2]}, Research: {f[3]}, Email: {f[4]}")

                elif intent == 'library':
                    cur.execute("SELECT title, author, subject, status, availability FROM books WHERE title ILIKE %s OR author ILIKE %s OR subject ILIKE %s", (search_term, search_term, search_term))
                    for b in cur.fetchall():
                        context_parts.append(f"LIBRARY BOOK: {b[0]} by {b[1]} (Subject: {b[2]}, Status: {b[3]}, Avail: {b[4]})")
                    
                    cur.execute("SELECT document_name, content FROM document_chunks WHERE content ILIKE %s OR document_name ILIKE %s", (search_term, search_term))
                    for c in cur.fetchall():
                        pdf_url = f"/static/uploads/notes/{c[0]}"
                        context_parts.append(f"TEACHER NOTE: {c[0]} | Content: {c[1][:400]} | Source: {pdf_url}")

                elif intent == 'placements':
                    cur.execute("SELECT name, company, package FROM alumni WHERE name ILIKE %s OR company ILIKE %s", (search_term, search_term))
                    for a in cur.fetchall():
                        context_parts.append(f"ALUMNI: {a[0]} placed at {a[1]} ({a[2]})")

                elif intent == 'academics':
                    cur.execute("SELECT full_name, code, faculty_name FROM timetable_subjects WHERE full_name ILIKE %s OR code ILIKE %s", (search_term, search_term))
                    for s in cur.fetchall():
                        context_parts.append(f"SUBJECT: {s[0]} ({s[1]}) - Faculty: {s[2]}")

                if len(context_parts) < 3:
                    cur.execute("SELECT title, content FROM website_content WHERE title ILIKE %s OR content ILIKE %s LIMIT 2", (search_term, search_term))
                    for w in cur.fetchall():
                        context_parts.append(f"INFO: {w[0]} - {w[1][:300]}")

    except Exception as e:
        print(f"Retrieval Error: {e}")
    finally:
        conn.close()

    return "\n".join(context_parts) if context_parts else "No specific database records found."

def generate_response(messages: List[dict], is_logged_in: bool = False) -> str:
    """
    Response generation via Groq/Llama. Accepts full message history from frontend.
    """
    if not messages:
        return "I didn't receive any message."
        
    user_query = messages[-1]['content']
    chat_history = messages[:-1]

    # Analyze Intent
    analysis = analyze_intent(user_query, chat_history)

    # Targeted Context Retrieval
    context = get_context_by_intent(analysis)

    login_instruction = (
        "The user is logged in. They can View and Download PDFs."
        if is_logged_in else
        "The user is NOT logged in. They can View but must be logged in to Download PDFs."
    )

    system_prompt = (
        "You are 'CS Connect Assistant', a professional AI for AISAT CSE department.\n"
        "RULES:\n"
        "1. MEMORY: Use CONVERSATION HISTORY to understand context. Resolve pronouns like 'him'/'them' from previous messages.\n"
        "2. NO JARGON: Never mention 'database', 'intent', 'records', or how you got the data.\n"
        "3. TARGETED: Answer ONLY based on the provided DATABASE CONTEXT and CONVERSATION HISTORY.\n"
        "4. SOURCE: Link PDFs as [Filename](/static/uploads/notes/filename.pdf).\n"
        "5. MANAGEMENT MATTERS: For sensitive decisions (e.g. 'who is next HOD'), reply: "
        "'These are matters handled by the Management and involve high-level decisions.'\n"
        f"6. {login_instruction}\n\n"
        f"DATABASE CONTEXT:\n{context}\n"
    )

    # Build messages list for Groq: system + prior history + current user query
    groq_messages = [{"role": "system", "content": system_prompt}]
    for m in chat_history[-6:]:
        if m.get('role') in ('user', 'assistant'):
            groq_messages.append({"role": m['role'], "content": str(m['content'])})
    groq_messages.append({"role": "user", "content": user_query})

    try:
        completion = client.chat.completions.create(
            messages=groq_messages,
            model=MODEL,
            temperature=0.4,
            max_tokens=800,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "I'm sorry, I'm having trouble retrieving information right now."

if __name__ == "__main__":
    test_msgs = [{"role": "user", "content": "What are the department stats?"}]
    print(generate_response(test_msgs, False))

