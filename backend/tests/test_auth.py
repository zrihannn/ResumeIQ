from app.core.security import hash_password
from app.core.config import settings
from app.models.entities import User


def test_authentication_and_role_permissions(client):
    previous = settings.auth_enabled
    settings.auth_enabled = True
    db = client.test_db()
    try:
        db.add_all([
            User(email="viewer@example.com", display_name="Read Only", password_hash=hash_password("viewer-password-123"), role="viewer"),
            User(email="recruiter@example.com", display_name="Recruiter", password_hash=hash_password("recruiter-password-123"), role="recruiter"),
            User(email="admin@example.com", display_name="Workspace Admin", password_hash=hash_password("admin-password-123"), role="admin"),
        ])
        db.commit()
    finally:
        db.close()

    try:
        assert client.get("/api/jobs").status_code == 401
        invalid = client.post("/api/auth/login", json={"email": "viewer@example.com", "password": "wrong-password"})
        assert invalid.status_code == 401

        viewer_login = client.post("/api/auth/login", json={"email": " VIEWER@example.com ", "password": "viewer-password-123"})
        assert viewer_login.status_code == 200
        viewer_token = viewer_login.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
        for path in ("/api/dashboard", "/api/candidates", "/api/jobs", "/api/applications", "/api/interviews", "/api/activity"):
            assert client.get(path, headers=viewer_headers).status_code == 200

        assert client.get("/api/auth/users", headers=viewer_headers).status_code == 403
        assert client.post("/api/auth/users", headers=viewer_headers, json={
            "email": "blocked@example.com", "display_name": "Blocked User",
            "password": "blocked-password-123", "role": "viewer",
        }).status_code == 403

        assert client.post("/api/jobs", headers=viewer_headers, json={
            "title": "Restricted role", "description": "A sufficiently long role description for permission testing."
        }).status_code == 403
        assert client.post("/api/applications", headers=viewer_headers, json={
            "candidate_id": 1, "job_id": 1
        }).status_code == 403
        assert client.post("/api/interviews", headers=viewer_headers, json={
            "application_id": 1, "title": "Restricted interview", "scheduled_at": "2026-11-10T10:00:00+05:30"
        }).status_code == 403

        recruiter_login = client.post("/api/auth/login", json={"email": "recruiter@example.com", "password": "recruiter-password-123"})
        assert recruiter_login.status_code == 200
        recruiter_headers = {"Authorization": f"Bearer {recruiter_login.json()['access_token']}"}
        created = client.post("/api/jobs", headers=recruiter_headers, json={
            "title": "Backend Engineer", "description": "Build reliable backend APIs and maintain data services."
        })
        assert created.status_code == 201, created.text
        activity = client.get("/api/activity", headers=recruiter_headers)
        assert activity.status_code == 200
        assert activity.json()[0]["actor_email"] == "recruiter@example.com"
        assert client.get("/api/auth/users", headers=recruiter_headers).status_code == 403

        admin_login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin-password-123"})
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        listed_users = client.get("/api/auth/users", headers=admin_headers)
        assert listed_users.status_code == 200
        assert {item["role"] for item in listed_users.json()} >= {"admin", "recruiter", "viewer"}

        invited = client.post("/api/auth/users", headers=admin_headers, json={
            "email": "observer@example.com",
            "display_name": "Workspace Observer",
            "password": "observer-password-123",
            "role": "viewer",
        })
        assert invited.status_code == 201, invited.text
        observer_login = client.post("/api/auth/login", json={
            "email": "observer@example.com", "password": "observer-password-123"
        })
        assert observer_login.status_code == 200
        assert observer_login.json()["user"]["role"] == "viewer"
    finally:
        settings.auth_enabled = previous


def test_password_hashing_and_token_header_validation():
    import base64
    import json
    from types import SimpleNamespace
    from app.core.security import create_access_token, decode_access_token, verify_password

    encoded = hash_password("a-long-test-password")
    assert verify_password("a-long-test-password", encoded)
    assert not verify_password("incorrect-password", encoded)

    user = SimpleNamespace(id=7, role="reviewer", email="reviewer@example.com")
    token = create_access_token(user)
    assert decode_access_token(token)["sub"] == "7"
    header, payload, signature = token.split(".")
    altered_header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    assert decode_access_token(f"{altered_header}.{payload}.{signature}") is None
