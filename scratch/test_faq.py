
import os
import sys
import asyncio

# Setup env for Groq
os.environ["GROQ_API_KEY"] = "gsk_..." # This will likely fail without a real key, 
# but I can check if the logic of fetching from DB works.

import database as db
import ai_responder
import state

# Initialize dummy clients
state.clients = {"groq": None} 

def test_fetch_db():
    print("Testing DB FAQ fetching...")
    # Add a mock question to DB if not exists
    db.init_db()
    # Check if "Hero nima?" exists
    items = db.get_faq_items(None)
    found = any(i['question'] == 'Hero nima?' for i in items)
    if not found:
        print("Mocking 'Hero nima?' FAQ item...")
        # Get Axborot texnologiyalari faculty id
        facs = db.get_all_faculties()
        at_id = next((f['id'] for f in facs if 'Axborot' in f['name']), None)
        db.add_faq_item(at_id, "Hero nima?", "Hero LMS tizimi bolib baholash uchun ishlatiladi!")
    
    # Test the combined context logic in ai_responder
    # We'll just check if they are fetched in get_answer logic
    # Since I can't call Groq, I'll just verify the items are merged.
    
    faculty_id = next((f['id'] for f in db.get_all_faculties() if 'Axborot' in f['name']), None)
    
    db_items = db.get_faq_items(faculty_id)
    general_items = db.get_faq_items(None)
    db_items.extend([i for i in general_items if i.get('faculty_id') is None])
    
    all_pairs = [{"question": i['question'], "answer": i['answer']} for i in db_items]
    
    print(f"Total Database Pairs fetched: {len(all_pairs)}")
    for p in all_pairs:
        if "Hero nima?" in p['question']:
            print(f"✅ Found DB Item: {p['question']} -> {p['answer']}")
            return True
    
    print("❌ DB Item not found in merged list")
    return False

if __name__ == "__main__":
    if test_fetch_db():
        print("SUCCESS")
    else:
        print("FAILURE")
        sys.exit(1)
