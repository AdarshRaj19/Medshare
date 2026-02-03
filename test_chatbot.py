"""
Test script to verify chatbot implementation
"""

import os
import sys
import django
from django.conf import settings
from pathlib import Path

# Add project directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import models and utilities
from app.models import ChatMessage, Medicine
from app.llm_integration import get_llm_response, LLMError
from django.contrib.auth.models import User
from django.utils import timezone

def test_chatbot_setup():
    """Test basic chatbot setup"""
    print("=" * 60)
    print("MEDSHARE AI CHATBOT - SETUP VERIFICATION")
    print("=" * 60)
    
    # 1. Check settings
    print("\n1. Configuration Check:")
    openai_key = getattr(settings, 'OPENAI_API_KEY', None)
    if openai_key:
        print(f"   ✓ OPENAI_API_KEY is configured: {openai_key[:10]}...")
    else:
        print("   ✗ OPENAI_API_KEY not configured")
        print("     Set OPENAI_API_KEY environment variable or in .env file")
    
    # 2. Check database tables
    print("\n2. Database Models Check:")
    try:
        msg_count = ChatMessage.objects.count()
        print(f"   ✓ ChatMessage table exists ({msg_count} messages)")
    except Exception as e:
        print(f"   ✗ Error accessing ChatMessage: {e}")
    
    # 3. Check if sample medicines exist
    print("\n3. Sample Data Check:")
    med_count = Medicine.objects.count()
    print(f"   ✓ Found {med_count} medicines in database")
    if med_count > 0:
        sample_meds = Medicine.objects.all()[:3]
        for med in sample_meds:
            print(f"     - {med.name} ({med.category.name if med.category else 'No category'})")
    
    # 4. Check views and URLs
    print("\n4. Routing Check:")
    from django.urls import reverse
    try:
        chatbot_url = reverse('medicine_chatbot')
        print(f"   ✓ Chatbot URL available: {chatbot_url}")
        
        chat_history_url = reverse('chat_history')
        print(f"   ✓ Chat history URL available: {chat_history_url}")
        
        chat_api_url = reverse('chat_message')
        print(f"   ✓ Chat API endpoint available: {chat_api_url}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 5. Check templates
    print("\n5. Template Check:")
    templates_to_check = [
        'medicine_chatbot.html',
        'chat_history.html'
    ]
    for template in templates_to_check:
        template_path = BASE_DIR / 'templates' / template
        if template_path.exists():
            print(f"   ✓ {template} exists")
        else:
            print(f"   ✗ {template} missing")
    
    # 6. LLM Integration Test
    print("\n6. LLM Integration Test:")
    try:
        from app.llm_integration import _init_openai
        client = _init_openai()
        if client:
            print("   ✓ OpenAI client initialized successfully")
        else:
            print("   ⚠ OpenAI client not available (API key may not be set)")
    except Exception as e:
        print(f"   ✗ Error initializing OpenAI: {e}")
    
    print("\n" + "=" * 60)
    print("SETUP VERIFICATION COMPLETE")
    print("=" * 60)
    
    print("\nNext Steps:")
    print("1. Set OPENAI_API_KEY environment variable or in .env file:")
    print("   - Get key from: https://platform.openai.com/account/api-keys")
    print("   - Add to .env: OPENAI_API_KEY=sk-your-key-here")
    print("\n2. Run the development server:")
    print("   python manage.py runserver")
    print("\n3. Access the chatbot:")
    print("   - Login at http://localhost:8000/login")
    print("   - Visit http://localhost:8000/chatbot/")
    print("   - Or click the robot icon in the navigation bar")
    print("\n4. Test features:")
    print("   - Ask questions about medicines")
    print("   - Select a medicine for context")
    print("   - View chat history")
    print("   - Rate responses as helpful/unhelpful")

if __name__ == '__main__':
    test_chatbot_setup()
