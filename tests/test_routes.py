"""
Unit tests for public routes and informational pages.
"""


def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'SKILL2HIRE' in response.data


def test_jobs_page(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert b'Senior Python Engineer' in response.data


def test_job_details_page(client):
    response = client.get('/jobs/1')
    assert response.status_code == 200
    assert b'Senior Python Engineer' in response.data
    assert b'Test Corp Pvt Ltd' in response.data


def test_job_not_found(client):
    response = client.get('/jobs/999999')
    assert response.status_code == 404


def test_companies_page(client):
    response = client.get('/companies')
    assert response.status_code == 200
    assert b'Test Corp Pvt Ltd' in response.data


def test_company_details(client):
    response = client.get('/companies/1')
    assert response.status_code == 200
    assert b'Test Corp Pvt Ltd' in response.data


def test_about_page(client):
    response = client.get('/about')
    assert response.status_code == 200
    assert b'About SKILL2HIRE' in response.data


def test_how_it_works_page(client):
    response = client.get('/how-it-works')
    assert response.status_code == 200
    assert b'How SKILL2HIRE Works' in response.data


def test_contact_page(client):
    response = client.get('/contact')
    assert response.status_code == 200
    assert b'Contact SKILL2HIRE' in response.data
