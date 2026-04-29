from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_reports_ok():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_seeded_product_lookup_by_barcode():
    response = client.get('/api/products/8901234567890')
    assert response.status_code == 200
    payload = response.json()
    assert payload['barcode'] == '8901234567890'
    assert payload['halal_status'] == 'halal'


def test_product_analysis_returns_ingredient_breakdown():
    response = client.get('/api/products/8901234567890/analyze')
    assert response.status_code == 200
    payload = response.json()
    assert payload['product']['barcode'] == '8901234567890'
    assert any(item['ingredient'] == 'E100' for item in payload['ingredients'])


def test_restaurant_listing_includes_seeded_entry():
    response = client.get('/api/restaurants')
    assert response.status_code == 200
    payload = response.json()
    assert payload['items'][0]['name'] == 'Baraka Grill'


def test_tracker_flow_and_alert_flow():
    tracker_response = client.post(
        '/api/users/me/tracker',
        json={'user_id': 1, 'product_barcode': '8901234567890'},
    )
    assert tracker_response.status_code == 201

    alerts_response = client.post(
        '/api/users/me/alerts',
        json={'user_id': 1, 'product_barcode': '8901234567890'},
    )
    assert alerts_response.status_code == 201

    tracker_listing = client.get('/api/users/me/tracker', params={'user_id': 1})
    assert tracker_listing.status_code == 200
    assert tracker_listing.json()['items'][0]['product_barcode'] == '8901234567890'

    alerts_listing = client.get('/api/users/me/alerts', params={'user_id': 1})
    assert alerts_listing.status_code == 200
    assert alerts_listing.json()['items'][0]['product_barcode'] == '8901234567890'


def test_pending_contribution_can_be_approved():
    submission = client.post(
        '/api/products',
        json={
            'user_id': 1,
            'barcode': '9998887776665',
            'name': 'Community Choco Bites',
            'brand': 'Ummah Foods',
            'ingredients': 'sugar, cocoa butter',
            'halal_status': 'halal',
            'certification_body': 'MUI',
            'cert_number': 'MUI-42',
            'source_url': 'https://example.org/community'
        },
    )
    assert submission.status_code == 201

    pending = client.get('/api/contribute/pending', params={'user_id': 1})
    assert pending.status_code == 200
    pending_items = pending.json()['items']
    target = next(item for item in pending_items if item['payload']['barcode'] == '9998887776665')

    approval = client.post(f"/api/contribute/{target['id']}/approve", params={'user_id': 1})
    assert approval.status_code == 200
    assert approval.json()['status'] == 'approved'

    product = client.get('/api/products/9998887776665')
    assert product.status_code == 200
    assert product.json()['name'] == 'Community Choco Bites'
