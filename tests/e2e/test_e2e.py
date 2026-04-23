import pytest
from uuid import uuid4
from playwright.sync_api import expect


def _base_url(fastapi_server: str) -> str:
    return fastapi_server.rstrip("/")


def _unique_user() -> dict:
    uid = uuid4().hex[:8]
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"test_{uid}@example.com",
        "username": f"testuser_{uid}",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }


def _register_via_ui(page, fastapi_server: str, user: dict) -> None:
    page.goto(f"{_base_url(fastapi_server)}/register")
    page.fill("#username", user["username"])
    page.fill("#email", user["email"])
    page.fill("#first_name", user["first_name"])
    page.fill("#last_name", user["last_name"])
    page.fill("#password", user["password"])
    page.fill("#confirm_password", user["confirm_password"])
    page.click('button[type="submit"]')
    page.wait_for_url("**/login", timeout=5000)


def _login_via_ui(page, fastapi_server: str, user: dict) -> None:
    page.goto(f"{_base_url(fastapi_server)}/login")
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard", timeout=5000)


def _register_and_login(page, fastapi_server: str, user: dict) -> None:
    _register_via_ui(page, fastapi_server, user)
    _login_via_ui(page, fastapi_server, user)


def _create_calculation(page, calc_type: str, inputs: str) -> None:
    """Submit the New Calculation form and wait for the table to update."""
    page.select_option("#calcType", calc_type)
    page.fill("#calcInputs", inputs)
    page.click('#calculationForm button[type="submit"]')
    expect(page.locator("#calculationsTable")).to_contain_text(calc_type, timeout=5000)


# ---------------------------------------------------------------------------
# Existing tests (preserved)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_home_page_loads(page, fastapi_server):
    page.goto(_base_url(fastapi_server))
    expect(page).to_have_title("Home")
    expect(page.locator("h1")).to_contain_text("Calculations App")


@pytest.mark.e2e
def test_login_page_loads(page, fastapi_server):
    page.goto(f"{_base_url(fastapi_server)}/login")
    expect(page).to_have_title("Login")
    expect(page.locator("#loginForm")).to_be_visible()


@pytest.mark.e2e
def test_register_page_loads(page, fastapi_server):
    page.goto(f"{_base_url(fastapi_server)}/register")
    expect(page).to_have_title("Register")
    expect(page.locator("#registrationForm")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_redirects_if_not_logged_in(page, fastapi_server):
    page.goto(f"{_base_url(fastapi_server)}/dashboard")
    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
def test_register_success(page, fastapi_server):
    user = _unique_user()
    page.goto(f"{_base_url(fastapi_server)}/register")

    for field in ["username", "email", "first_name", "last_name", "password", "confirm_password"]:
        page.fill(f"#{field}", user[field])

    page.click('button[type="submit"]')
    expect(page.locator("#successAlert")).to_be_visible()
    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
@pytest.mark.parametrize("username,password,confirm", [
    ("ab", "SecurePass123!", "SecurePass123!"),
    ("validuser", "weak", "weak"),
    ("validuser", "pass1", "pass2"),
])
def test_register_validation_errors(page, fastapi_server, username, password, confirm):
    page.goto(f"{_base_url(fastapi_server)}/register")
    page.fill("#username", username)
    page.fill("#email", "test@example.com")
    page.fill("#first_name", "Test")
    page.fill("#last_name", "User")
    page.fill("#password", password)
    page.fill("#confirm_password", confirm)
    page.click('button[type="submit"]')

    expect(page.locator("#errorAlert")).to_be_visible()


@pytest.mark.e2e
def test_register_duplicate_username(page, fastapi_server):
    user = _unique_user()
    _register_via_ui(page, fastapi_server, user)

    page.goto(f"{_base_url(fastapi_server)}/register")
    for field in user:
        page.fill(f"#{field}", user[field])
    page.click('button[type="submit"]')

    expect(page.locator("#errorAlert")).to_be_visible()


@pytest.mark.e2e
def test_login_success(page, fastapi_server):
    user = _unique_user()
    _register_via_ui(page, fastapi_server, user)
    _login_via_ui(page, fastapi_server, user)

    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")


@pytest.mark.e2e
def test_login_remember_me(page, fastapi_server):
    user = _unique_user()
    _register_via_ui(page, fastapi_server, user)

    page.goto(f"{_base_url(fastapi_server)}/login")
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.check("#remember")
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard", timeout=5000)

    page.goto(f"{_base_url(fastapi_server)}/login")
    expect(page.locator("#username")).to_have_value(user["username"])


@pytest.mark.e2e
def test_dashboard_empty_state(page, fastapi_server):
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    expect(page.locator("#calculationsTable")).to_contain_text("No calculations found", timeout=5000)


@pytest.mark.e2e
@pytest.mark.parametrize("calc_type, inputs, expected", [
    ("addition", "10,5", "15"),
    ("subtraction", "20,8", "12"),
    ("multiplication", "4,5", "20"),
    ("division", "100,4", "25"),
])
def test_dashboard_create_calculations(page, fastapi_server, calc_type, inputs, expected):
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    page.select_option("#calcType", calc_type)
    page.fill("#calcInputs", inputs)
    page.click('#calculationForm button[type="submit"]')

    expect(page.locator("#calculationsTable")).to_contain_text(calc_type, timeout=5000)
    expect(page.locator("#calculationsTable")).to_contain_text(expected)


@pytest.mark.e2e
def test_dashboard_invalid_inputs(page, fastapi_server):
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    page.fill("#calcInputs", "42")
    page.click('#calculationForm button[type="submit"]')

    expect(page.locator("#errorAlert")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_delete(page, fastapi_server):
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    page.select_option("#calcType", "addition")
    page.fill("#calcInputs", "3,7")
    page.click('#calculationForm button[type="submit"]')

    page.on("dialog", lambda dialog: dialog.accept())
    page.locator(".delete-calc").first.click()

    expect(page.locator("#calculationsTable")).to_contain_text("No calculations found", timeout=5000)


# ---------------------------------------------------------------------------
# index.html — home page content
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_home_page_features_section(page, fastapi_server):
    """Three feature cards are present on the home page."""
    page.goto(_base_url(fastapi_server))
    expect(page.locator("h2", has_text="Simple Calculations")).to_be_visible()
    expect(page.locator("h2", has_text="Save History")).to_be_visible()
    expect(page.locator("h2", has_text="Edit & Update")).to_be_visible()


@pytest.mark.e2e
def test_home_page_how_it_works_section(page, fastapi_server):
    """'How It Works' three-step section is rendered."""
    page.goto(_base_url(fastapi_server))
    expect(page.locator("h2", has_text="How It Works")).to_be_visible()
    expect(page.locator("h3", has_text="Create Account")).to_be_visible()
    expect(page.locator("h3", has_text="Enter Values")).to_be_visible()
    expect(page.locator("h3", has_text="View Results")).to_be_visible()


@pytest.mark.e2e
def test_home_page_cta_section(page, fastapi_server):
    """Bottom call-to-action section is present."""
    page.goto(_base_url(fastapi_server))
    expect(page.locator("h2", has_text="Ready to Get Started?")).to_be_visible()
    expect(page.locator("a", has_text="Create Free Account")).to_be_visible()


# ---------------------------------------------------------------------------
# layout.html — header / footer / toast / nav
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_layout_brand_link_logged_out(page, fastapi_server):
    """Brand link points to / when logged out."""
    page.goto(_base_url(fastapi_server))
    href = page.locator("#brandLink").get_attribute("href")
    assert href.endswith("/")


@pytest.mark.e2e
def test_layout_brand_link_logged_in_points_to_dashboard(page, fastapi_server):
    """After login, the brand link in the header points to /dashboard."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    expect(page.locator("#brandLink")).to_have_attribute("href", "/dashboard")


@pytest.mark.e2e
def test_layout_logout_button_hidden_when_logged_out(page, fastapi_server):
    """Logout button is hidden for unauthenticated visitors."""
    page.goto(_base_url(fastapi_server))
    expect(page.locator("#layoutLogoutBtn")).to_be_hidden()


@pytest.mark.e2e
def test_layout_logout_button_visible_when_logged_in(page, fastapi_server):
    """Logout button is visible after login."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    expect(page.locator("#layoutLogoutBtn")).to_be_visible()


@pytest.mark.e2e
def test_layout_welcome_message_shown_when_logged_in(page, fastapi_server):
    """Header shows 'Welcome, <username>!' when logged in."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    expect(page.locator("#layoutUserWelcome")).to_contain_text(f"Welcome, {user['username']}!")


@pytest.mark.e2e
def test_layout_logout_confirm_redirects_to_login(page, fastapi_server):
    """Confirming the logout dialog from the layout header redirects to /login."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    page.on("dialog", lambda d: d.accept())
    page.locator("#layoutLogoutBtn").click()

    page.wait_for_url("**/login", timeout=5000)
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/login")


@pytest.mark.e2e
def test_layout_logout_cancel_stays_on_page(page, fastapi_server):
    """Cancelling the logout dialog keeps the user on the dashboard."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    page.on("dialog", lambda d: d.dismiss())
    page.locator("#layoutLogoutBtn").click()

    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")


@pytest.mark.e2e
def test_layout_footer_links_present(page, fastapi_server):
    """Footer contains Privacy Policy, Terms of Service, and Help Center links."""
    page.goto(_base_url(fastapi_server))
    expect(page.locator("footer a", has_text="Privacy Policy")).to_be_visible()
    expect(page.locator("footer a", has_text="Terms of Service")).to_be_visible()
    expect(page.locator("footer a", has_text="Help Center")).to_be_visible()


@pytest.mark.e2e
def test_layout_toast_container_present(page, fastapi_server):
    """Toast notification container exists in the DOM on every page."""
    page.goto(_base_url(fastapi_server))
    expect(page.locator("#toastContainer")).to_be_attached()


# ---------------------------------------------------------------------------
# login.html — additional cases
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_login_wrong_password_shows_error(page, fastapi_server):
    """Incorrect password shows the error alert and stays on /login."""
    user = _unique_user()
    _register_via_ui(page, fastapi_server, user)

    page.goto(f"{_base_url(fastapi_server)}/login")
    page.fill("#username", user["username"])
    page.fill("#password", "WrongPassword9!")
    page.click('button[type="submit"]')

    expect(page.locator("#errorAlert")).to_be_visible()
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/login")


@pytest.mark.e2e
def test_login_empty_fields_shows_error(page, fastapi_server):
    """Submitting the login form empty shows a client-side error."""
    page.goto(f"{_base_url(fastapi_server)}/login")
    page.click('button[type="submit"]', force=True)
    validation = page.locator("#username").evaluate("el => el.validationMessage")
    assert validation != ""


@pytest.mark.e2e
def test_login_page_has_register_link(page, fastapi_server):
    """Login page has a 'Register now' link pointing to /register."""
    page.goto(f"{_base_url(fastapi_server)}/login")
    expect(page.locator('a[href="/register"]')).to_be_visible()


# ---------------------------------------------------------------------------
# register.html — additional cases
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_register_page_has_login_link(page, fastapi_server):
    """Register page has a 'Log in' link pointing to /login."""
    page.goto(f"{_base_url(fastapi_server)}/register")
    expect(page.locator('a[href="/login"]')).to_be_visible()


@pytest.mark.e2e
def test_register_invalid_email_shows_error(page, fastapi_server):
    """An invalid email address triggers a client-side validation error."""
    page.goto(f"{_base_url(fastapi_server)}/register")
    page.fill("#username", "validuser")
    page.fill("#email", "not-an-email")
    page.fill("#first_name", "Test")
    page.fill("#last_name", "User")
    page.fill("#password", "SecurePass123!")
    page.fill("#confirm_password", "SecurePass123!")
    page.click('button[type="submit"]', force=True)
    validation = page.locator("#email").evaluate("el => el.validationMessage")
    assert validation != ""


# ---------------------------------------------------------------------------
# dashboard.html — additional cases
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_dashboard_title_and_heading(page, fastapi_server):
    """Dashboard page has the correct title and section headings."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    expect(page).to_have_title("Dashboard")
    expect(page.locator("h2", has_text="New Calculation")).to_be_visible()
    expect(page.locator("h2", has_text="Calculation History")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_calc_type_dropdown_has_all_options(page, fastapi_server):
    """The operation type dropdown contains all four options."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    for value in ["addition", "subtraction", "multiplication", "division"]:
        expect(page.locator(f'#calcType option[value="{value}"]')).to_have_count(1)


@pytest.mark.e2e
def test_dashboard_success_alert_on_create(page, fastapi_server):
    """Creating a calculation shows a success alert with the result."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    page.select_option("#calcType", "addition")
    page.fill("#calcInputs", "6,4")
    page.click('#calculationForm button[type="submit"]')

    expect(page.locator("#successAlert")).to_be_visible(timeout=5000)
    expect(page.locator("#successMessage")).to_contain_text("10")


@pytest.mark.e2e
def test_dashboard_row_has_view_and_edit_links(page, fastapi_server):
    """Each table row has View and Edit links alongside the Delete button."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "addition", "1,2")

    row = page.locator("#calculationsTable tr").first
    expect(row.locator("a", has_text="View")).to_be_visible()
    expect(row.locator("a", has_text="Edit")).to_be_visible()
    expect(row.locator("button.delete-calc")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_delete_cancel_keeps_row(page, fastapi_server):
    """Cancelling the delete confirmation dialog leaves the row in place."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "multiplication", "3,3")

    page.on("dialog", lambda d: d.dismiss())
    page.locator(".delete-calc").first.click()

    expect(page.locator("#calculationsTable")).to_contain_text("multiplication")


@pytest.mark.e2e
def test_dashboard_multiple_calculations_all_appear(page, fastapi_server):
    """Creating two different calculations shows both rows in the table."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)

    _create_calculation(page, "addition", "1,1")
    _create_calculation(page, "subtraction", "10,3")

    expect(page.locator("#calculationsTable")).to_contain_text("addition")
    expect(page.locator("#calculationsTable")).to_contain_text("subtraction")
    expect(page.locator("#calculationsTable tr")).to_have_count(2)


# ---------------------------------------------------------------------------
# view_calculation.html
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_view_calculation_redirects_if_not_logged_in(page, fastapi_server):
    """Accessing /dashboard/view/<id> without auth redirects to /login."""
    page.goto(f"{_base_url(fastapi_server)}/dashboard/view/00000000-0000-0000-0000-000000000000")
    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
def test_view_calculation_shows_details(page, fastapi_server):
    """View page loads the correct calculation details card."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "multiplication", "4,5")

    page.locator("a", has_text="View").first.click()
    page.wait_for_url("**/dashboard/view/**", timeout=5000)

    expect(page).to_have_title("View Calculation")
    expect(page.locator("#calculationCard")).to_be_visible(timeout=5000)
    expect(page.locator("#calculationCard")).to_contain_text("multiplication")
    expect(page.locator("#calculationCard")).to_contain_text("20")


@pytest.mark.e2e
def test_view_calculation_has_edit_and_back_buttons(page, fastapi_server):
    """View page has an 'Edit Calculation' link and 'Back to Dashboard' link."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "addition", "7,3")

    page.locator("a", has_text="View").first.click()
    page.wait_for_url("**/dashboard/view/**", timeout=5000)
    expect(page.locator("#calculationCard")).to_be_visible(timeout=5000)

    expect(page.locator("#editLink")).to_be_visible()
    expect(page.locator("a", has_text="Back to Dashboard")).to_be_visible()


@pytest.mark.e2e
def test_view_calculation_delete_redirects_to_dashboard(page, fastapi_server):
    """Deleting from the view page redirects back to /dashboard."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "division", "50,5")

    page.locator("a", has_text="View").first.click()
    page.wait_for_url("**/dashboard/view/**", timeout=5000)
    expect(page.locator("#calculationCard")).to_be_visible(timeout=5000)

    page.on("dialog", lambda d: d.accept())
    page.locator("#deleteBtn").click()

    page.wait_for_url("**/dashboard", timeout=5000)
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")


@pytest.mark.e2e
def test_view_calculation_back_link_navigates_to_dashboard(page, fastapi_server):
    """'Back to Dashboard' link navigates back to the dashboard."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "subtraction", "9,4")

    page.locator("a", has_text="View").first.click()
    page.wait_for_url("**/dashboard/view/**", timeout=5000)
    expect(page.locator("#calculationCard")).to_be_visible(timeout=5000)

    page.locator("a", has_text="Back to Dashboard").click()
    page.wait_for_url("**/dashboard", timeout=5000)
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")


# ---------------------------------------------------------------------------
# edit_calculation.html
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_edit_calculation_redirects_if_not_logged_in(page, fastapi_server):
    """Accessing /dashboard/edit/<id> without auth redirects to /login."""
    page.goto(f"{_base_url(fastapi_server)}/dashboard/edit/00000000-0000-0000-0000-000000000000")
    page.wait_for_url("**/login", timeout=5000)


@pytest.mark.e2e
def test_edit_calculation_page_loads_with_prefilled_values(page, fastapi_server):
    """Edit page loads, shows the form, and pre-fills type and inputs."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "addition", "3,4")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)

    expect(page).to_have_title("Edit Calculation")
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)
    expect(page.locator("#calcType")).to_have_value("addition")
    expect(page.locator("#calcInputs")).not_to_have_value("")


@pytest.mark.e2e
def test_edit_calculation_type_is_readonly(page, fastapi_server):
    """The operation type field on the edit page is read-only."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "multiplication", "2,6")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    expect(page.locator("#calcType")).to_have_attribute("readonly", "")


@pytest.mark.e2e
def test_edit_calculation_save_updates_result(page, fastapi_server):
    """Changing the inputs and saving redirects to the view page with the new result."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "addition", "1,2")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    page.fill("#calcInputs", "10, 20")
    page.click('#editCalculationForm button[type="submit"]')

    page.wait_for_url("**/dashboard/view/**", timeout=5000)
    expect(page.locator("#calculationCard")).to_be_visible(timeout=5000)
    expect(page.locator("#calculationCard")).to_contain_text("30")


@pytest.mark.e2e
def test_edit_calculation_too_few_inputs_shows_error(page, fastapi_server):
    """Submitting a single number on the edit form shows a validation error."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "addition", "5,5")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    page.fill("#calcInputs", "99")
    page.click('#editCalculationForm button[type="submit"]')

    expect(page.locator("#errorAlert")).to_be_visible(timeout=5000)


@pytest.mark.e2e
def test_edit_calculation_live_preview_updates(page, fastapi_server):
    """Typing new inputs updates the result preview in real time."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "addition", "1,1")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    page.fill("#calcInputs", "50, 50")
    expect(page.locator("#previewResult")).to_contain_text("100", timeout=3000)


@pytest.mark.e2e
def test_edit_calculation_cancel_returns_to_dashboard(page, fastapi_server):
    """Clicking 'Cancel' on the edit page navigates back to /dashboard."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "subtraction", "10,3")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    page.locator("a", has_text="Cancel").click()
    page.wait_for_url("**/dashboard", timeout=5000)
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")


@pytest.mark.e2e
def test_edit_calculation_view_details_link(page, fastapi_server):
    """'View Details' link on the edit page navigates to the view page."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "division", "20,4")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    page.locator("a", has_text="View Details").click()
    page.wait_for_url("**/dashboard/view/**", timeout=5000)
    expect(page).to_have_title("View Calculation")


@pytest.mark.e2e
def test_edit_calculation_breadcrumb_links(page, fastapi_server):
    """Breadcrumb 'Dashboard' link navigates back to /dashboard."""
    user = _unique_user()
    _register_and_login(page, fastapi_server, user)
    _create_calculation(page, "multiplication", "5,5")

    page.locator("a", has_text="Edit").first.click()
    page.wait_for_url("**/dashboard/edit/**", timeout=5000)
    expect(page.locator("#editCard")).to_be_visible(timeout=5000)

    page.locator("nav[aria-label='Breadcrumb'] a", has_text="Dashboard").click()
    page.wait_for_url("**/dashboard", timeout=5000)
    expect(page).to_have_url(f"{_base_url(fastapi_server)}/dashboard")
