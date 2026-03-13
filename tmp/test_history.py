import os
import sys

# Add current directory to path
sys.path.append(r"c:\Users\LENOVO\Desktop\Mini project\cs_connect")

import llm_engine

def test_chat_flow():
    history = []
    
    print("\n--- TEST 1: Initial Query ---")
    q1 = "Who is Prof. Dhanya George?"
    res1 = llm_engine.generate_response(q1, history, is_logged_in=True)
    print(f"User: {q1}")
    print(f"AI: {res1}")
    
    history.append({"role": "user", "content": q1})
    history.append({"role": "assistant", "content": res1})
    
    print("\n--- TEST 2: Follow-up with Pronoun ---")
    q2 = "What is her email and research?"
    res2 = llm_engine.generate_response(q2, history, is_logged_in=True)
    print(f"User: {q2}")
    print(f"AI: {res2}")

    history.append({"role": "user", "content": q2})
    history.append({"role": "assistant", "content": res2})
    
    print("\n--- TEST 3: Subject Shift ---")
    q3 = "List some library books about Math."
    res3 = llm_engine.generate_response(q3, history, is_logged_in=True)
    print(f"User: {q3}")
    print(f"AI: {res3}")

    history.append({"role": "user", "content": q3})
    history.append({"role": "assistant", "content": res3})

    print("\n--- TEST 5: Location Query ---")
    q5 = "Where is AISAT located?"
    res5 = llm_engine.generate_response(q5, history, is_logged_in=False)
    print(f"User: {q5}")
    print(f"AI: {res5}")

    print("\n--- TEST 6: Sensitive Management Query ---")
    q6 = "Who is the next HOD for CSE?"
    res6 = llm_engine.generate_response(q6, history, is_logged_in=True)
    print(f"User: {q6}")
    print(f"AI: {res6}")

if __name__ == "__main__":
    test_chat_flow()
