import pytest
from uuid import uuid4
from playwright.sync_api import expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_url(fastapi_server: str) -> str:
    return fastapi_server.rstrip("/")


def _goto(page, fastapi_server, path=""):
    page.goto(f"{_base_url(fastapi_server)}{path}")


def _unique_user():
    uid = uuid4().hex[:8]
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"test_{uid}@example.com",
        "username": f"testuser_{uid}",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }


def _fill_form(page, data: dict):
    for key, value in data.items():
        page.fill(f"#{key}", value)


def _submit(page, selector='button[type="submit"]'):
    page.click(selector)


def _register(page, fastapi_server, user):
    _goto(page, fastapi_server, "/register")
    _fill_form(page, user)
    _submit(page)
    page.wait_for_url("**/login", timeout=5000)


def _login(page, fastapi_server, user, remember=False):
    _goto(page, fastapi_server, "/login")
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    if remember:
        page.check("#remember")
    _submit(page)
    page.wait_for_url("**/dashboard", timeout=5000)


def _auth(page, fastapi_server, user):
    _register(page, fastapi_server, user)
    _login(page, fastapi_server, user)


def _submit_calc(page, calc_type, inputs):
    page.select_option("#calcType", calc_type)
    page.fill("#calcInputs", inputs)
    _submit(page, '#calculationForm button[type="submit"]')


def _create_calc(page, calc_type, inputs):
    _submit_calc(page, calc_type, inputs)
    expect(page.locator("#calculationsTable")).to_contain_text(calc_type, timeout=5000)


# ---------------------------------------------------------------------------
# Basic Pages
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_home_page_loads(page, fastapi_server):
    _goto(page, fastapi_server)
    expect(page).to_have_title("Home")
    expect(page.locator("h1")).to_contain_text("Calculations App")


@pytest.mark.e2e
def test_login_page_loads(page, fastapi_server):
    _goto(page, fastapi_server, "/login")
    expect(page).to_have_title("Login")
    expect(page.locator("#loginForm")).to_be_visible()


@pytest.mark.e2e
def test_register_page_loads(page, fastapi_server):
    _goto(page, fastapi_server, "/register")
    expect(page).to_have_title("Register")
    expect(page.locator("#registrationForm")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_redirects_if_not_logged_in(page, fastapi_server):
    _goto(page, fastapi_server, "/dashboard")
    page.wait_for_url("**/login", timeout=5000)


# ---------------------------------------------------------------------------
# Auth Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_register_success(page, fastapi_server):
    user = _unique_user()
    _goto(page, fastapi_server, "/register")
    _fill_form(page, user)
    _submit(page)

    expect(page.locator("#successAlert")).to_be_visible()
    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
@pytest.mark.parametrize("username,password,confirm", [
    ("ab", "SecurePass123!", "SecurePass123!"),
    ("validuser", "weak", "weak"),
    ("validuser", "pass1", "pass2"),
])
def test_register_validation_errors(page, fastapi_server, username, password, confirm):
    _goto(page, fastapi_server, "/register")
    _fill_form(page, {
        "username": username,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": password,
        "confirm_password": confirm,
    })
    _submit(page)
    expect(page.locator("#errorAlert")).to_be_visible()


@pytest.mark.e2e
def test_login_success(page, fastapi_server):
    user = _unique_user()
    _auth(page, fastapi_server, user)
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")


@pytest.mark.e2e
def test_login_remember_me(page, fastapi_server):
    user = _unique_user()
    _register(page, fastapi_server, user)

    _login(page, fastapi_server, user, remember=True)
    _goto(page, fastapi_server, "/login")

    expect(page.locator("#username")).to_have_value(user["username"])


# ---------------------------------------------------------------------------
# Dashboard Core
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_dashboard_empty_state(page, fastapi_server):
    user = _unique_user()
    _auth(page, fastapi_server, user)
    expect(page.locator("#calculationsTable")).to_contain_text("No calculations found")


@pytest.mark.e2e
@pytest.mark.parametrize("calc_type, inputs, expected", [
    ("addition", "10,5", "15"),
    ("subtraction", "20,8", "12"),
    ("multiplication", "4,5", "20"),
    ("division", "100,4", "25"),
])
def test_dashboard_create_calculations(page, fastapi_server, calc_type, inputs, expected):
    user = _unique_user()
    _auth(page, fastapi_server, user)

    _submit_calc(page, calc_type, inputs)

    table = page.locator("#calculationsTable")
    expect(table).to_contain_text(calc_type)
    expect(table).to_contain_text(expected)


@pytest.mark.e2e
def test_dashboard_invalid_inputs(page, fastapi_server):
    user = _unique_user()
    _auth(page, fastapi_server, user)

    page.fill("#calcInputs", "42")
    _submit(page, '#calculationForm button[type="submit"]')

    expect(page.locator("#errorAlert")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_delete(page, fastapi_server):
    user = _unique_user()
    _auth(page, fastapi_server, user)

    _create_calc(page, "addition", "3,7")

    page.on("dialog", lambda d: d.accept())
    page.locator(".delete-calc").first.click()

    expect(page.locator("#calculationsTable")).to_contain_text("No calculations found")


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_layout_logout_visibility(page, fastapi_server):
    _goto(page, fastapi_server)
    expect(page.locator("#layoutLogoutBtn")).to_be_hidden()

    user = _unique_user()
    _auth(page, fastapi_server, user)
    expect(page.locator("#layoutLogoutBtn")).to_be_visible()


# ---------------------------------------------------------------------------
# View / Edit (sample condensed pattern)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_view_calculation_flow(page, fastapi_server):
    user = _unique_user()
    _auth(page, fastapi_server, user)
    _create_calc(page, "multiplication", "4,5")

    page.locator("a", has_text="View").first.click()
    page.wait_for_url("**/dashboard/view/**")

    card = page.locator("#calculationCard")
    expect(card).to_be_visible()
    expect(card).to_contain_text("20")


@pytest.mark.e2e
def test_edit_calculation_flow(page, fastapi_server):
    user = _unique_user()
    _auth(page, fastapi_server, user)
    _create_calc(page, "addition", "1,2")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**")

    page.fill("#calcInputs", "10,20")
    _submit(page, '#editCalculationForm button[type="submit"]')

    page.wait_for_url("**/dashboard/view/**")
    expect(page.locator("#calculationCard")).to_contain_text("30")


# ---------------------------------------------------------------------------
# New Operations (fully reused helpers)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.parametrize("calc_type,inputs,expected", [
    ("power", "2,10", "1024"),
    ("modulus", "17,5", "2"),
    ("root", "27,3", "3"),
    ("integer_division", "17,3", "5"),
    ("abs_difference", "3,10", "7"),
    ("percentage", "25,200", "12.5"),
])
def test_new_operations(page, fastapi_server, calc_type, inputs, expected):
    user = _unique_user()
    _auth(page, fastapi_server, user)

    _submit_calc(page, calc_type, inputs)

    table = page.locator("#calculationsTable")
    expect(table).to_contain_text(calc_type)
    expect(table).to_contain_text(expected)