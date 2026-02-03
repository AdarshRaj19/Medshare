"""
Chatbot views and API endpoints for medicine Q&A using LLM
"""

from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import logging

from .llm_integration import get_llm_response, LLMError
from .models import Medicine, ChatMessage

logger = logging.getLogger(__name__)


@login_required
def medicine_chatbot(request):
    """
    Medicine Q&A chatbot page
    Users can ask questions about medicines, donations, usage, etc.
    """
    context = {
        'medicines': Medicine.objects.filter(status='available')[:5],
    }
    return render(request, 'medicine_chatbot.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message_api(request):
    """
    API endpoint for chatbot messages
    Receives user message, queries LLM, returns response
    
    Request JSON:
    {
        "message": "What is paracetamol used for?",
        "medicine_id": 123  # optional context
    }
    
    Response JSON:
    {
        "success": true,
        "response": "Paracetamol is commonly used for...",
        "timestamp": "2026-02-02T10:30:00Z"
    }
    """
    try:
        user_message = request.data.get('message', '').strip()
        medicine_id = request.data.get('medicine_id')
        
        if not user_message:
            return Response({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Build context from medicine if provided
        context = ""
        if medicine_id:
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                context = f"Medicine context: {medicine.name}, Category: {medicine.category.name}, Expiry: {medicine.expiry_date}"
            except Medicine.DoesNotExist:
                pass
        
        # Get LLM response
        try:
            llm_response = get_llm_response(user_message, context=context, temperature=0.7)
        except LLMError as e:
            # Return error response for unexpected failures
            return Response({
                'success': False,
                'error': f'Could not generate response: {str(e)}'
            }, status=503)
        
        # Save chat message to database (optional, for history)
        try:
            ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=llm_response,
                medicine_id=medicine_id
            )
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")
            # Don't fail the response if DB save fails
        
        return Response({
            'success': True,
            'response': llm_response,
            'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Chatbot API error: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred processing your message'
        }, status=500)


@login_required
def chat_history(request):
    """
    View chat history for current user
    """
    messages = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    context = {
        'chat_history': messages,
    }
    return render(request, 'chat_history.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history_api(request):
    """
    API endpoint to fetch chat history (JSON)
    
    Query params:
        - limit: number of messages (default: 20, max: 100)
        - medicine_id: filter by medicine (optional)
    """
    limit = min(int(request.GET.get('limit', 20)), 100)
    medicine_id = request.GET.get('medicine_id')
    
    query = ChatMessage.objects.filter(user=request.user).order_by('-created_at')
    
    if medicine_id:
        query = query.filter(medicine_id=medicine_id)
    
    messages = query[:limit]
    
    data = [{
        'id': msg.id,
        'message': msg.message,
        'response': msg.response,
        'medicine': msg.medicine.name if msg.medicine else None,
        'created_at': msg.created_at.isoformat(),
    } for msg in messages]
    
    return Response({
        'success': True,
        'messages': data,
        'count': len(data)
    })


@login_required
@require_http_methods(["POST"])
def clear_chat_history(request):
    """
    Clear chat history for current user
    """
    ChatMessage.objects.filter(user=request.user).delete()
    return JsonResponse({
        'success': True,
        'message': 'Chat history cleared'
    })


@api_view(['POST'])
def quick_medicine_answer(request):
    """
    Public API for quick medicine Q&A (no login required)
    Rate limited to prevent abuse
    
    Request: {"question": "Is aspirin safe for kids?"}
    Response: {"answer": "..."}
    """
    question = request.data.get('question', '').strip()
    
    if not question:
        return Response({'error': 'Question required'}, status=400)
    
    # Rate limit (simple IP-based)
    client_ip = get_client_ip(request)
    cache_key = f'quick_qa_{client_ip}'
    
    from django.core.cache import cache
    if cache.get(cache_key):
        return Response({
            'error': 'Rate limit exceeded. Try again in 30 seconds.'
        }, status=429)
    
    try:
        answer = get_llm_response(
            question,
            context="This is a public Q&A service. Be brief and helpful.",
            temperature=0.5
        )
        
        # Set rate limit
        cache.set(cache_key, True, 30)
        
        return Response({
            'success': True,
            'question': question,
            'answer': answer
        })
    
    except LLMError as e:
        return Response({
            'error': str(e)
        }, status=503)


def get_client_ip(request):
    """Get client IP from request (handles proxies)"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


__all__ = [
    'medicine_chatbot',
    'chat_message_api',
    'chat_history',
    'chat_history_api',
    'clear_chat_history',
    'quick_medicine_answer',
]
