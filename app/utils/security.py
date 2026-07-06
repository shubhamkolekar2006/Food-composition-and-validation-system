import time
import re
from flask import request, jsonify
from functools import wraps
from werkzeug.utils import secure_filename

# Stateless in-memory cache for IP-based rate limiting
_rate_limit_cache = {}

def rate_limit(limit=60, period=60):
    """
    Stateless IP-based rate limiter decorator.
    limit: max number of requests allowed in the period
    period: duration in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time.time()
            
            # Clean old timestamps
            if ip in _rate_limit_cache:
                _rate_limit_cache[ip] = [t for t in _rate_limit_cache[ip] if now - t < period]
            else:
                _rate_limit_cache[ip] = []
                
            if len(_rate_limit_cache[ip]) >= limit:
                return jsonify({'error': 'Rate limit exceeded. Please wait before trying again.'}), 429
                
            _rate_limit_cache[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def allowed_file(filename):
    """
    Enforces secure image uploads for OCR scans.
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def sanitize_input(text):
    """
    Sanitizes string inputs to prevent HTML injection.
    """
    if not text:
        return ""
    # Strip whitespace
    text = str(text).strip()
    # Strip HTML tags
    clean_text = re.sub(r'<[^>]*>', '', text)
    return clean_text
