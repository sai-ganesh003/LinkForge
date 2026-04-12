import pytest
from app import create_app, db
from app.models import URL, User

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.get_json()['status'] == 'ok'


def test_shorten_url(client):
    res = client.post('/shorten', json={
        'original_url': 'https://www.google.com'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert 'short_code' in data
    assert len(data['short_code']) == 6
    assert data['original_url'] == 'https://www.google.com'


def test_shorten_url_missing_field(client):
    res = client.post('/shorten', json={})
    assert res.status_code == 400


def test_shorten_with_expiry(client):
    res = client.post('/shorten', json={
        'original_url': 'https://www.github.com',
        'expiry_days': 7
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['expires_at'] is not None


def test_redirect(client):
    res = client.post('/shorten', json={
        'original_url': 'https://www.google.com'
    })
    short_code = res.get_json()['short_code']
    res2 = client.get(f'/{short_code}', follow_redirects=False)
    assert res2.status_code in [301, 302]


def test_redirect_not_found(client):
    res = client.get('/notexist')
    assert res.status_code == 404


def test_analytics(client):
    res = client.post('/shorten', json={
        'original_url': 'https://www.google.com'
    })
    short_code = res.get_json()['short_code']
    res2 = client.get(f'/analytics/{short_code}')
    assert res2.status_code == 200
    data = res2.get_json()
    assert data['short_code'] == short_code


def test_analytics_not_found(client):
    res = client.get('/analytics/notexist')
    assert res.status_code == 404


def test_register(client):
    res = client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123'
    })
    assert res.status_code == 201


def test_register_duplicate_email(client):
    client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123'
    })
    res = client.post('/register', json={
        'username': 'testuser2',
        'email': 'test@example.com',
        'password': 'test123'
    })
    assert res.status_code == 409


def test_login(client):
    client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123'
    })
    res = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'test123'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert 'access_token' in data
    assert 'refresh_token' in data


def test_login_wrong_password(client):
    client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123'
    })
    res = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    assert res.status_code == 401


def test_short_code_uniqueness(client):
    codes = set()
    for _ in range(10):
        res = client.post('/shorten', json={
            'original_url': 'https://www.google.com'
        })
        codes.add(res.get_json()['short_code'])
    assert len(codes) == 10