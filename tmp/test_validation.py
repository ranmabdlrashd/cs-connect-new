import sys
import os
import json
import logging

# Add current directory to path to import llm_engine
sys.path.append(os.path.abspath('.'))

try:
    from llm_engine import validate_intent_response, ALLOWED_INTENTS
except ImportError:
    print("Error: Could not import llm_engine. Make sure to run this script from the project root.")
    sys.exit(1)

# Configure logging to see warnings
logging.basicConfig(level=logging.INFO)

def test_validation():
    test_cases = [
        {
            "name": "Valid JSON",
            "input": '{"intent": "faculty", "keywords": ["sharma", "research"]}',
            "expected": {"intent": "faculty", "keywords": ["sharma", "research"]}
        },
        {
            "name": "Invalid JSON",
            "input": 'Not a JSON string',
            "expected": {"intent": "general", "keywords": []}
        },
        {
            "name": "Missing keywords",
            "input": '{"intent": "notes"}',
            "expected": {"intent": "notes", "keywords": []}
        },
        {
            "name": "Missing intent",
            "input": '{"keywords": ["test"]}',
            "expected": {"intent": "general", "keywords": ["test"]}
        },
        {
            "name": "Invalid Intent Value",
            "input": '{"intent": "unknown_intent", "keywords": ["test"]}',
            "expected": {"intent": "general", "keywords": ["test"]}
        },
        {
            "name": "Misspelled Intent (Normalized)",
            "input": '{"intent": "  FACULTY  ", "keywords": ["smith"]}',
            "expected": {"intent": "faculty", "keywords": ["smith"]}
        },
        {
            "name": "Malformed Keywords (not a list)",
            "input": '{"intent": "notes", "keywords": "single_keyword"}',
            "expected": {"intent": "notes", "keywords": []}
        },
        {
            "name": "Keywords with empty strings",
            "input": '{"intent": "notes", "keywords": ["math", "", "  ", "physics"]}',
            "expected": {"intent": "notes", "keywords": ["math", "physics"]}
        },
        {
            "name": "Markdown wrapped JSON",
            "input": '```json\n{"intent": "cgpa", "keywords": ["marks"]}\n```',
            "expected": {"intent": "cgpa", "keywords": ["marks"]}
        }
    ]

    print(f"Running {len(test_cases)} test cases...\n")
    passed = 0
    for case in test_cases:
        print(f"Testing: {case['name']}")
        result = validate_intent_response(case['input'])
        if result == case['expected']:
            print("  [PASS]")
            passed += 1
        else:
            print(f"  [FAIL]")
            print(f"    Input: {case['input']}")
            print(f"    Expected: {case['expected']}")
            print(f"    Got: {result}")
        print("-" * 30)

    print(f"\nFinal Result: {passed}/{len(test_cases)} cases passed.")
    if passed == len(test_cases):
        print("All tests passed successfully!")
    else:
        print("Some tests failed. Please review the output.")

if __name__ == "__main__":
    test_validation()
