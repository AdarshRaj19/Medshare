import re

with open('static/css/style.css', 'r') as f:
    content = f.read()

# Remove all footer-professional, footer-, newsletter-, cta-, and back-to-top-professional CSS rules
# Pattern to match CSS selectors and their rules
patterns = [
    r'\.footer-professional\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    r'\[data-theme="dark"\]\s*\.footer-[a-z-]*\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    r'\.footer-[a-z-]*\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    r'\.newsletter-[a-z-]*\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    r'\.cta-[a-z-]*\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    r'\.back-to-top-professional[a-z-]*\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
    r'\[data-theme="dark"\]\s*\.back-to-top-professional\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
]

for pattern in patterns:
    content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

# Remove excessive blank lines
content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

with open('static/css/style.css', 'w') as f:
    f.write(content)

print('Footer CSS successfully removed')
