"""
LLM Integration for MedShare
Handles OpenAI API calls for medicine Q&A chatbot and auto-generation features
"""

import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client (delayed import to handle missing module gracefully)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', getattr(settings, 'OPENAI_API_KEY', None))
client = None

def _init_openai():
    """Lazy initialize OpenAI client"""
    global client
    if client is not None:
        return client
    
    try:
        from openai import OpenAI
        if OPENAI_API_KEY:
            client = OpenAI(api_key=OPENAI_API_KEY)
            return client
        else:
            logger.warning("OPENAI_API_KEY not set. LLM features will not work.")
            return None
    except ImportError:
        logger.warning("OpenAI module not installed. Run: pip install openai")
        return None


class LLMError(Exception):
    """Custom exception for LLM operations"""
    pass


def get_llm_response(user_message: str, context: str = "", temperature: float = 0.7) -> str:
    """
    Get response from OpenAI GPT for medicine Q&A
    
    Args:
        user_message: User's question
        context: Optional context (e.g., medicine details, NGO info)
        temperature: Creativity level (0-1, lower = more deterministic)
    
    Returns:
        LLM response as string
    
    Raises:
        LLMError: If API call fails
    """
    client_instance = _init_openai()
    if not client_instance:
        # Offline / development fallback: return a concise, safe canned response
        logger.warning("OpenAI not configured - returning offline mock response.")

        # Simple keyword-based heuristics to make responses slightly contextual
        q = user_message.lower()
        canned = {
            'paracetamol': 'Paracetamol (acetaminophen) is commonly used to relieve pain and reduce fever. Follow dosing instructions on the package and consult a healthcare professional for children or chronic conditions.',
            'aspirin': 'Aspirin is used for pain relief and anti-inflammatory purposes and may be used in low doses for certain heart conditions. It is not generally recommended for children with viral illnesses; consult a doctor.',
            'ibuprofen': 'Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used for pain, fever, and inflammation. Take with food to reduce stomach upset and consult a healthcare professional if you have ulcers or kidney issues.',
            'donate': 'To donate medicines, ensure they are unopened, unexpired, and in original packaging. Check the MedShare donation guidelines on the Donations page for eligible items and drop-off locations.',
            'side effect': 'Common side effects depend on the medicine; check the leaflet for a full list. If you experience severe reactions (difficulty breathing, swelling, rash), seek emergency medical attention.',
        }

        for k, v in canned.items():
            if k in q:
                return v

        # Generic fallback
        return (
            "I’m running in offline mode without access to the AI service. "
            "I can provide general guidance: consult the medicine leaflet or a healthcare professional for specific medical advice. "
            "If you need the AI assistant enabled, ask the site administrator to configure the OpenAI API key."
        )
    
    try:
        system_prompt = """You are a helpful medical information assistant for MedShare, 
a medicine donation platform. You provide accurate, concise information about medicines,
donations, and NGO services. Always be professional and encourage users to consult 
healthcare professionals for medical advice. Keep responses under 300 words."""
        
        if context:
            system_prompt += f"\n\nContext: {context}"
        
        response = client_instance.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=500,
            top_p=0.9,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        err_msg = str(e)
        logger.error(f"OpenAI API error: {err_msg}")
        
        # If quota exceeded or billing issue, use fallback
        if 'quota' in err_msg.lower() or '429' in err_msg or 'billing' in err_msg.lower():
            logger.info("OpenAI quota exceeded - using offline fallback mode")
            # Return a helpful fallback instead of erroring out
            q = user_message.lower()
            canned = {
                'paracetamol': 'Paracetamol (acetaminophen) is commonly used to relieve pain and reduce fever. Follow dosing instructions on the package and consult a healthcare professional for children or chronic conditions.',
                'aspirin': 'Aspirin is used for pain relief and anti-inflammatory purposes. It is not generally recommended for children with viral illnesses; consult a doctor.',
                'ibuprofen': 'Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used for pain, fever, and inflammation. Take with food to reduce stomach upset.',
                'donate': 'To donate medicines, ensure they are unopened, unexpired, and in original packaging. Check the MedShare donation guidelines.',
                'side effect': 'Common side effects depend on the medicine; check the leaflet. Seek medical attention for severe reactions.',
            }
            for k, v in canned.items():
                if k in q:
                    return v
            return "I'm temporarily unavailable due to service limits, but you can consult the medicine leaflet or contact a healthcare professional for medical information."
        
        raise LLMError(f"Failed to get LLM response: {err_msg}")


def generate_emergency_alert_description(
    medicine_name: str, 
    quantity_needed: int, 
    unit: str,
    patient_count: int = None,
    priority: str = "medium",
    location: str = None
) -> str:
    """
    Auto-generate compelling emergency alert description using LLM
    
    Args:
        medicine_name: Name of medicine needed
        quantity_needed: Quantity required
        unit: Unit of measurement (tablets, ml, etc)
        patient_count: Number of patients affected (optional)
        priority: Priority level (low, medium, high, critical)
        location: Location of NGO (optional)
    
    Returns:
        Generated description string
    """
    client_instance = _init_openai()
    if not client_instance:
        logger.warning("OpenAI not configured; returning default description.")
        return f"Urgent need for {quantity_needed} {unit} of {medicine_name}."
    
    try:
        prompt = f"""Generate a compelling and professional emergency alert description for a medicine shortage.

Medicine: {medicine_name}
Quantity Needed: {quantity_needed} {unit}
Priority: {priority.upper()}
{f'Patients Affected: {patient_count}' if patient_count else ''}
{f'Location: {location}' if location else ''}

Create a brief (1-2 sentences), urgent but professional description that will motivate donors to respond quickly.
Include the medicine name, quantity, and urgency without being melodramatic."""
        
        response = client_instance.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional medical emergency alert writer for an NGO. Write clear, compelling alerts that drive immediate action."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,  # Slightly more creative
            max_tokens=150,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Emergency alert generation error: {str(e)}")
        # Fallback to simple description
        return f"Urgent need for {quantity_needed} {unit} of {medicine_name}. Priority: {priority}."


def chat_stream(messages: list, temperature: float = 0.7):
    """
    Stream responses from OpenAI for real-time chat (for future streaming implementation)
    
    Args:
        messages: List of message dicts [{"role": "user", "content": "..."}, ...]
        temperature: Creativity level
    
    Yields:
        Streamed response chunks
    """
    client_instance = _init_openai()
    if not client_instance:
        # Provide a simple non-streaming fallback chunk
        yield "I’m running in offline mode and cannot stream responses. Please enable the OpenAI API key for full functionality."
        return
    
    try:
        system_prompt = """You are a helpful medical information assistant for MedShare. 
Provide accurate, concise information about medicines. Encourage consulting healthcare professionals."""
        
        # Add system message if not present
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        
        with client_instance.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
            max_tokens=500,
            stream=True,
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    
    except Exception as e:
        logger.error(f"Chat stream error: {str(e)}")
        yield f"Error: {str(e)}"


def validate_medicine_info(medicine_name: str, medicine_details: dict) -> dict:
    """
    Use LLM to validate and enrich medicine information
    
    Args:
        medicine_name: Name of medicine
        medicine_details: Dict with medicine info (expiry, quantity, etc)
    
    Returns:
        Validated/enriched info dict with warnings if any
    """
    client_instance = _init_openai()
    if not client_instance:
        return {"valid": True, "warnings": []}
    
    try:
        prompt = f"""Validate this medicine information for safety:
        
Medicine: {medicine_name}
Details: {medicine_details}

Check for:
1. Valid medicine name
2. Reasonable quantity
3. Realistic expiry date
4. Any safety concerns

Respond in JSON format: {{"valid": bool, "warnings": [list of strings], "suggestions": [list of strings]}}"""
        
        response = client_instance.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a pharmaceutical safety validator. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Deterministic
            max_tokens=300,
        )
        
        import json
        result = response.choices[0].message.content.strip()
        return json.loads(result)
    
    except Exception as e:
        logger.error(f"Medicine validation error: {str(e)}")
        return {"valid": True, "warnings": [], "suggestions": []}


# Export functions
__all__ = [
    'get_llm_response',
    'generate_emergency_alert_description',
    'chat_stream',
    'validate_medicine_info',
    'LLMError',
]
