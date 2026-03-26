import os
import sys
from unittest.mock import MagicMock, patch

# Mock database and groq before importing llm_engine
sys.modules['database'] = MagicMock()
sys.modules['groq'] = MagicMock()

import llm_engine

def test_prompt_construction():
    print("Testing prompt construction with study material...")
    
    # Use a dictionary as the input to build_safe_context (which calls item.get)
    item = {
        "title": "ML_Notes.pdf",
        "category": "STUDY MATERIAL",
        "details": "Machine Learning introduction",
        "extra": ""
    }
    
    # Mock get_safe_pdf_url to return a dummy URL
    with patch('llm_engine.get_safe_pdf_url', return_value="/static/uploads/notes/ML_Notes.pdf"):
        context = llm_engine.build_safe_context([item])
        
        print("\nGenerated Context:")
        print(context)
        
        # Check if Resource URL is in context
        if "Resource URL: /static/uploads/notes/ML_Notes.pdf" in context:
            print("\nSUCCESS: Resource URL found in context.")
        else:
            print("\nFAILURE: Resource URL NOT found in context.")
            
        # Check the system prompt
        with patch('llm_engine.fetch_db_context', return_value=context):
            with patch('llm_engine.analyze_intent', return_value='{}'):
                with patch('llm_engine.validate_intent_response', return_value={"intent": "notes", "keywords": ["ml"]}):
                    with patch('llm_engine.client.chat.completions.create') as mock_create:
                        llm_engine.generate_chatbot_response("ml notes", [])
                        
                        # Get the system prompt passed to create
                        args, kwargs = mock_create.call_args
                        system_msg = kwargs['messages'][0]['content']
                        
                        print("\nGenerated System Prompt:")
                        print("-" * 20)
                        print(system_msg)
                        print("-" * 20)
                        
                        if "[Download Notes](PDF_URL)" in system_msg:
                            print("\nSUCCESS: Guided prompt rules found in system prompt.")
                        else:
                            print("\nFAILURE: Guided prompt rules NOT found in system prompt.")

if __name__ == "__main__":
    # Mock BASE_DIR for the test
    llm_engine.BASE_DIR = "/tmp" 
    test_prompt_construction()
