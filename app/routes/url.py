from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timedelta
from app import db, redis_client
from app.models import URL, User
from app.utils.shortener import generate_short_code
from app.utils.rate_limiter import rate_limit

url = Blueprint('url', __name__)

@url.route('/shorten', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
def shorten_url():
    """
    Shorten a URL
    ---
    tags:
      - URL
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - original_url
          properties:
            original_url:
              type: string
              example: https://www.google.com
            expiry_days:
              type: integer
              example: 7
    responses:
      201:
        description: URL shortened successfully
      400:
        description: Missing URL
    """
    data = request.get_json()

    if not data or not data.get('original_url'):
        return jsonify({"error": "original_url is required"}), 400

    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass

    short_code = generate_short_code()
    expiry_days = data.get('expiry_days')
    expires_at = datetime.utcnow() + timedelta(days=expiry_days) if expiry_days else None

    new_url = URL(
        original_url=data['original_url'],
        short_code=short_code,
        user_id=user_id,
        expires_at=expires_at
    )

    db.session.add(new_url)
    db.session.commit()

    redis_client.setex(f"url:{short_code}", 3600, data['original_url'])

    return jsonify({
        "short_code": short_code,
        "short_url": f"{request.host_url}{short_code}",
        "original_url": data['original_url'],
        "expires_at": expires_at.isoformat() if expires_at else None
    }), 201


@url.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    """
    Redirect to original URL
    ---
    tags:
      - URL
    parameters:
      - in: path
        name: short_code
        type: string
        required: true
    responses:
      302:
        description: Redirect to original URL
      404:
        description: URL not found or expired
    """
    cached = redis_client.get(f"url:{short_code}")
    if cached:
        url_record = URL.query.filter_by(short_code=short_code).first()
        if url_record:
            url_record.clicks += 1
            db.session.commit()
        return redirect(cached.decode('utf-8'))

    url_record = URL.query.filter_by(short_code=short_code, is_active=True).first()

    if not url_record:
        return jsonify({"error": "URL not found"}), 404

    if url_record.expires_at and url_record.expires_at < datetime.utcnow():
        url_record.is_active = False
        db.session.commit()
        return jsonify({"error": "URL has expired"}), 404

    url_record.clicks += 1
    db.session.commit()

    redis_client.setex(f"url:{short_code}", 3600, url_record.original_url)

    return redirect(url_record.original_url)


@url.route('/analytics/<short_code>', methods=['GET'])
def get_analytics(short_code):
    """
    Get click analytics for a short URL
    ---
    tags:
      - URL
    parameters:
      - in: path
        name: short_code
        type: string
        required: true
    responses:
      200:
        description: Analytics data
      404:
        description: URL not found
    """
    url_record = URL.query.filter_by(short_code=short_code).first()
    if not url_record:
        return jsonify({"error": "URL not found"}), 404

    return jsonify({
        "short_code": url_record.short_code,
        "original_url": url_record.original_url,
        "clicks": url_record.clicks,
        "created_at": url_record.created_at.isoformat(),
        "expires_at": url_record.expires_at.isoformat() if url_record.expires_at else None,
        "is_active": url_record.is_active
    }), 200


@url.route('/urls', methods=['GET'])
@jwt_required()
def get_my_urls():
    """
    Get all URLs created by logged in user
    ---
    tags:
      - URL
    security:
      - Bearer: []
    responses:
      200:
        description: List of user's URLs
      401:
        description: Unauthorized
    """
    identity = get_jwt_identity()
    urls = URL.query.filter_by(user_id=int(identity)).all()
    return jsonify([{
        "short_code": u.short_code,
        "short_url": f"{request.host_url}{u.short_code}",
        "original_url": u.original_url,
        "clicks": u.clicks,
        "created_at": u.created_at.isoformat(),
        "expires_at": u.expires_at.isoformat() if u.expires_at else None,
        "is_active": u.is_active
    } for u in urls]), 200


@url.route('/urls/<short_code>', methods=['DELETE'])
@jwt_required()
def delete_url(short_code):
    """
    Delete a short URL
    ---
    tags:
      - URL
    security:
      - Bearer: []
    parameters:
      - in: path
        name: short_code
        type: string
        required: true
    responses:
      200:
        description: URL deleted
      403:
        description: Not your URL
      404:
        description: URL not found
    """
    identity = get_jwt_identity()
    url_record = URL.query.filter_by(short_code=short_code).first()

    if not url_record:
        return jsonify({"error": "URL not found"}), 404

    if url_record.user_id != int(identity):
        return jsonify({"error": "you can only delete your own URLs"}), 403

    redis_client.delete(f"url:{short_code}")
    db.session.delete(url_record)
    db.session.commit()

    return jsonify({"message": "URL deleted successfully"}), 200