"""
Integration tests for GET /stats — full HTTP layer through TestClient.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Helpers (mirror test_main.py style)
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def base_url(fastapi_server):
    return fastapi_server.rstrip("/")


def _register(client, base_url, data):
    r = client.post(f"{base_url}/auth/register", json=data)
    assert r.status_code == 201, r.text
    return r.json()


def _login(client, base_url, username, password):
    r = client.post(f"{base_url}/auth/login",
                    json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _user_and_token(client, base_url):
    suffix = uuid4().hex[:8]
    data = {
        "first_name": "Stats",
        "last_name":  "Tester",
        "email":      f"stats_{suffix}@example.com",
        "username":   f"stats_{suffix}",
        "password":   "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }
    _register(client, base_url, data)
    token = _login(client, base_url, data["username"], data["password"])
    return data, token


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create(client, base_url, token, type_, inputs):
    r = client.post(f"{base_url}/calculations",
                    json={"type": type_, "inputs": inputs},
                    headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Authentication guard
# ---------------------------------------------------------------------------

class TestStatsAuth:
    def test_unauthenticated_returns_401(self, client, base_url):
        r = client.get(f"{base_url}/stats")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client, base_url):
        r = client.get(f"{base_url}/stats",
                       headers={"Authorization": "Bearer not.a.real.token"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

class TestStatsEmpty:
    def test_returns_200(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        r = client.get(f"{base_url}/stats", headers=_auth(token))
        assert r.status_code == 200

    def test_total_calculations_zero(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_calculations"] == 0

    def test_total_operands_zero(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_operands"] == 0

    def test_avg_operands_zero(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["avg_operands_per_calculation"] == 0.0

    def test_avg_result_none(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["avg_result"] is None

    def test_breakdown_empty_list(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["operations_breakdown"] == []

    def test_most_used_none(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["most_used_operation"] is None

    def test_timestamps_none(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["last_calculation_at"] is None
        assert body["first_calculation_at"] is None


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

class TestStatsResponseShape:
    def test_all_required_fields_present(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        required = {
            "total_calculations", "total_operands",
            "avg_operands_per_calculation", "avg_result",
            "max_result", "min_result",
            "operations_breakdown", "most_used_operation",
            "least_used_operation", "last_calculation_at",
            "first_calculation_at",
        }
        assert required.issubset(body.keys())

    def test_breakdown_item_has_type_count_percentage(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [1, 2])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        item = body["operations_breakdown"][0]
        assert "type" in item
        assert "count" in item
        assert "percentage" in item


# ---------------------------------------------------------------------------
# After one calculation
# ---------------------------------------------------------------------------

class TestStatsOneCalculation:
    def setup_method(self):
        self.client = TestClient(app)

    def test_total_calculations_one(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [3, 7])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_calculations"] == 1

    def test_total_operands_two(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [3, 7])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_operands"] == 2

    def test_avg_operands_two(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [3, 7])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["avg_operands_per_calculation"] == 2.0

    def test_avg_result_correct(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [3, 7])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["avg_result"] == pytest.approx(10.0)

    def test_min_max_result_same(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [3, 7])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["min_result"] == pytest.approx(10.0)
        assert body["max_result"] == pytest.approx(10.0)

    def test_breakdown_single_type(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [3, 7])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert len(body["operations_breakdown"]) == 1
        assert body["operations_breakdown"][0]["type"] == "addition"
        assert body["operations_breakdown"][0]["count"] == 1
        assert body["operations_breakdown"][0]["percentage"] == pytest.approx(100.0)

    def test_most_and_least_used_same(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "multiplication", [3, 4])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["most_used_operation"] == "multiplication"
        assert body["least_used_operation"] == "multiplication"

    def test_timestamps_populated(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition", [1, 2])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["first_calculation_at"] is not None
        assert body["last_calculation_at"] is not None


# ---------------------------------------------------------------------------
# Multiple calculations
# ---------------------------------------------------------------------------

class TestStatsMultipleCalculations:
    def test_counts_all_operations(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        for _ in range(3):
            _create(client, base_url, token, "addition", [1, 2])
        for _ in range(2):
            _create(client, base_url, token, "division", [10, 2])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_calculations"] == 5

    def test_most_used_correct(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        for _ in range(4):
            _create(client, base_url, token, "addition", [1, 2])
        _create(client, base_url, token, "subtraction", [5, 3])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["most_used_operation"] == "addition"

    def test_least_used_correct(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        for _ in range(4):
            _create(client, base_url, token, "addition", [1, 2])
        _create(client, base_url, token, "subtraction", [5, 3])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["least_used_operation"] == "subtraction"

    def test_breakdown_sorted_by_count_desc(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        for _ in range(3):
            _create(client, base_url, token, "multiplication", [2, 3])
        _create(client, base_url, token, "division", [6, 2])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        counts = [b["count"] for b in body["operations_breakdown"]]
        assert counts == sorted(counts, reverse=True)

    def test_percentages_sum_near_100(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition",    [1, 2])
        _create(client, base_url, token, "subtraction", [5, 3])
        _create(client, base_url, token, "division",    [6, 2])
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        total_pct = sum(b["percentage"] for b in body["operations_breakdown"])
        assert abs(total_pct - 100.0) < 0.5

    def test_total_operands_accumulates(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition",       [1, 2, 3])  # 3 operands
        _create(client, base_url, token, "multiplication", [4, 5])     # 2 operands
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_operands"] == 5

    def test_avg_result_across_types(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition",    [1, 9])   # result=10
        _create(client, base_url, token, "subtraction", [20, 10]) # result=10
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["avg_result"] == pytest.approx(10.0)

    def test_max_result(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition",       [100, 200])  # 300
        _create(client, base_url, token, "multiplication", [2, 3])      # 6
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["max_result"] == pytest.approx(300.0)

    def test_min_result(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        _create(client, base_url, token, "addition",       [100, 200])  # 300
        _create(client, base_url, token, "multiplication", [2, 3])      # 6
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["min_result"] == pytest.approx(6.0)


# ---------------------------------------------------------------------------
# User isolation
# ---------------------------------------------------------------------------

class TestStatsUserIsolation:
    def test_user_only_sees_own_stats(self, client, base_url):
        _, token_a = _user_and_token(client, base_url)
        _, token_b = _user_and_token(client, base_url)

        # User A creates 5 calculations
        for _ in range(5):
            _create(client, base_url, token_a, "addition", [1, 2])

        # User B creates 1 calculation
        _create(client, base_url, token_b, "multiplication", [3, 4])

        body_a = client.get(f"{base_url}/stats", headers=_auth(token_a)).json()
        body_b = client.get(f"{base_url}/stats", headers=_auth(token_b)).json()

        assert body_a["total_calculations"] == 5
        assert body_b["total_calculations"] == 1

    def test_deleted_calc_not_counted(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        calc = _create(client, base_url, token, "addition", [1, 2])
        # delete it
        client.delete(f"{base_url}/calculations/{calc['id']}",
                      headers=_auth(token))
        body = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body["total_calculations"] == 0

    def test_stats_updates_after_new_calc(self, client, base_url):
        _, token = _user_and_token(client, base_url)
        body_before = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        _create(client, base_url, token, "addition", [1, 2])
        body_after = client.get(f"{base_url}/stats", headers=_auth(token)).json()
        assert body_after["total_calculations"] == body_before["total_calculations"] + 1


# ---------------------------------------------------------------------------
# Stats HTML page route
# ---------------------------------------------------------------------------

class TestStatsPageRoute:
    def test_stats_page_returns_200(self, client, base_url):
        r = client.get(f"{base_url}/dashboard/stats")
        assert r.status_code == 200

    def test_stats_page_is_html(self, client, base_url):
        r = client.get(f"{base_url}/dashboard/stats")
        assert "text/html" in r.headers["content-type"]

    def test_stats_page_contains_stats_content_id(self, client, base_url):
        r = client.get(f"{base_url}/dashboard/stats")
        assert "statsContent" in r.text

    def test_stats_page_contains_breakdown_table(self, client, base_url):
        r = client.get(f"{base_url}/dashboard/stats")
        assert "breakdownTable" in r.text
