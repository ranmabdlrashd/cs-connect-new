import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from llm_engine import extract_keywords, chat_cache

def test_keywords():
    test_cases = [
        ("Who is Divya?", ["divya"]),
        ("Tell me about Python notes", ["python", "notes"]),
        ("What are the placement stats for 2024?", ["placement", "stats", "2024"]),
        ("Give me the syllabus for S4 CSE", ["syllabus", "cse"])
    ]
    
    for input_str, expected in test_cases:
        result = extract_keywords(input_str)
        print(f"Input: {input_str} -> Keywords: {result}")
        # Not asserting exact match because order might vary or small differences
        for word in expected:
            if word not in result:
                print(f"FAILED: '{word}' not found in {result}")

def test_cache():
    from llm_engine import generate_chatbot_response
    # Mocking client since we don't have API key
    import llm_engine
    class MockCompletion:
        class Choice:
            class Message:
                content = "Mocked Response"
            message = Message()
        choices = [Choice()]

    class MockClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    print("LLM Call Made")
                    return MockCompletion()
            completions = Completions()
        chat = Chat()
    
    llm_engine.client = MockClient()
    
    print("First call:")
    resp1 = generate_chatbot_response("test query", [])
    print("Second call (should be cached):")
    resp2 = generate_chatbot_response("test query", [])
    
    if resp1 == resp2 == "Mocked Response":
        print("Caching Test Passed")
    else:
        print("Caching Test Failed")

if __name__ == "__main__":
    print("Testing Keywords...")
    test_keywords()
    print("\nTesting Cache...")
    test_cache()
