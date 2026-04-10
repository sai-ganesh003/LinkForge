from flask import request, jsonify
from functools import wraps
from app import redis_client

def rate_limit(max_requests=10, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            key = f"rate_limit:{ip}:{request.endpoint}"
            
            current = redis_client.get(key)
            
            if current and int(current) >= max_requests:
                return jsonify({
                    "error": "rate limit exceeded",
                    "message": f"max {max_requests} requests per {window_seconds} seconds"
                }), 429
            
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            pipe.execute()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator