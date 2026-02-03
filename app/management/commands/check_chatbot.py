from django.core.management.base import BaseCommand
from django.test import Client
import json


class Command(BaseCommand):
    help = "Check chatbot page and API endpoints without requiring OPENAI_API_KEY"

    def handle(self, *args, **options):
        client = Client()

        self.stdout.write('Checking /chatbot/ (GET)')
        try:
            resp = client.get('/chatbot/')
            self.stdout.write(f'GET /chatbot/ -> {resp.status_code}')
        except Exception as e:
            self.stdout.write(f'GET /chatbot/ error: {e}')

        self.stdout.write('Checking /api/chat/message/ (POST)')
        payload = {'message': 'Health chatbot test message'}
        try:
            resp = client.post('/api/chat/message/', data=json.dumps(payload), content_type='application/json')
            self.stdout.write(f'POST /api/chat/message/ -> {resp.status_code}')
            # Try to pretty-print JSON response
            try:
                data = json.loads(resp.content.decode('utf-8'))
                self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception:
                self.stdout.write(resp.content.decode('utf-8', errors='replace'))
        except Exception as e:
            self.stdout.write(f'POST /api/chat/message/ error: {e}')
