import os
import sys
# Add parent dir to path
sys.path.append(os.getcwd())

import file_loader
import ai_responder

def test_loading():
    print("Loading Knowledge Base...")
    kb = file_loader.load_knowledge_base()
    print(f"Total KB Length: {len(kb)} chars")
    
    print("\nAttempting to parse Q&A pairs...")
    pairs = ai_responder.parse_qa_pairs(kb)
    
    print(f"\nParsed {len(pairs)} pairs.")
    if pairs:
        print("\nFirst 3 pairs:")
        for i, p in enumerate(pairs[:3]):
            print(f"[{i}] Q: {p['question'][:100]}...")
            # print(f"    A: {p['answer'][:100]}...")
    else:
        print("\nWARNING: No Q&A pairs found! The AI will mostly rely on general knowledge or fail academic questions.")
        print("\nSample KB content (first 500 chars):")
        print(kb[:500])

if __name__ == "__main__":
    test_loading()
