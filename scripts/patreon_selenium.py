#!/usr/bin/env python3
"""Create a Patreon draft from a Daily note using a signed-in Edge session.

Patreon has no write API. This script launches Edge with a dedicated persistent
Patreon profile, opens the creator page, creates a post, and fills its title,
body, tags, free audience, and publish date. It stops at a verified draft
unless --publish is supplied explicitly.

First install Selenium. The first run opens a separate Edge profile at
~/Library/Application Support/PatreonSelenium. Sign into Patreon there; later
runs reuse that authenticated profile.

    python3 -m pip install --user selenium

Usage:
    python3 scripts/patreon_selenium.py "Daily/2026-10-18 (A New Way of Being).md"
    python3 scripts/patreon_selenium.py "Daily/2026-10-18 (A New Way of Being).md" --publish
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as conditions
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    selenium_import_error = True
else:
    selenium_import_error = False


CREATOR_URL = "https://www.patreon.com/c/ManOfGodSA"
# Patreon hydrates its creator navigation after the initial page load. Give
# the authenticated dashboard enough time before treating a control as absent.
WAIT_SECONDS = 90
EDGE_BINARY = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
PROFILE_DIR = Path.home() / "Library/Application Support/PatreonSelenium"


def wait_for(driver, locator):
    """Return a visible element or fail with the control that could not be found."""
    try:
        return WebDriverWait(driver, WAIT_SECONDS).until(
            conditions.visibility_of_element_located(locator)
        )
    except TimeoutException:
        raise RuntimeError(f"Timed out waiting for Patreon control: {locator}") from None


def click_visible(driver, locator):
    element = wait_for(driver, locator)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    driver.execute_script("arguments[0].click();", element)
    return element


def first_visible(driver, locators):
    """Try Patreon UI variants without relying on build-specific CSS class names."""
    end = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < end:
        for locator in locators:
            for element in driver.find_elements(*locator):
                if element.is_displayed() and element.is_enabled():
                    return element
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for one of: {locators}")


def set_text(driver, element, value, name):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    element.click()
    element.send_keys(Keys.COMMAND, "a")
    element.send_keys(value)
    actual = element.get_attribute("value") or element.get_attribute("textContent") or ""
    if actual.strip() != value.strip():
        raise RuntimeError(f"Could not confirm {name}; expected {value!r}, got {actual!r}")


def set_editor_html(driver, editor, html):
    """Use the editor's input event so Patreon persists rich HTML as a draft."""
    driver.execute_script(
        """
        const editor = arguments[0], html = arguments[1];
        editor.focus();
        editor.innerHTML = html;
        editor.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText'}));
        editor.dispatchEvent(new Event('change', {bubbles: true}));
        """,
        editor,
        html,
    )
    expected = driver.execute_script("return arguments[0].innerText.trim();", editor)
    if not expected:
        raise RuntimeError("Could not confirm the post body in Patreon editor")


def add_tags(driver, tags):
    trigger = first_visible(driver, [
        (By.XPATH, "//*[self::button or self::div][contains(normalize-space(), 'Add tags')]"),
        (By.XPATH, "//*[@aria-label='Add tags']"),
    ])
    trigger.click()
    for tag in tags:
        field = first_visible(driver, [
            (By.CSS_SELECTOR, "input[placeholder*='tag' i]"),
            (By.XPATH, "//input[@type='text']"),
        ])
        field.send_keys(tag)
        field.send_keys(Keys.ENTER)
        if not driver.find_elements(By.XPATH, f"//*[normalize-space()={json.dumps(tag)}]"):
            raise RuntimeError(f"Could not confirm Patreon tag: {tag}")


def select_free_audience(driver):
    free = first_visible(driver, [
        (By.XPATH, "//*[self::button or self::label or @role='radio'][contains(translate(normalize-space(), 'FREE', 'free'), 'free')]")
    ])
    free.click()
    # Patreon may render a radio state or only the selected label, so confirm both.
    checked = free.get_attribute("aria-checked")
    if checked not in ("true", None) and "free" not in free.text.lower():
        raise RuntimeError("Could not confirm that the audience is free")


def set_publish_date(driver, date):
    date_button = first_visible(driver, [
        (By.XPATH, "//*[self::button or self::div][contains(normalize-space(), 'Set publish date')]"),
        (By.XPATH, "//*[self::button or self::div][contains(normalize-space(), 'Publish date')]"),
    ])
    date_button.click()
    field = first_visible(driver, [
        (By.CSS_SELECTOR, "input[type='date']"),
        (By.XPATH, "//input[contains(@placeholder, 'date') or contains(@aria-label, 'date')]"),
    ])
    set_text(driver, field, date, "publish date")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("note", type=Path)
    parser.add_argument("--publish", action="store_true", help="publish after every field has been verified")
    args = parser.parse_args()

    if selenium_import_error:
        sys.exit("Selenium is required. Install it with: python3 -m pip install --user selenium")

    repo = Path(__file__).resolve().parent.parent
    output = Path("/tmp") / f"patreon-{args.note.stem[:10]}"
    subprocess.run(
        [sys.executable, "scripts/patreon_post.py", str(args.note), "--out", str(output)],
        cwd=repo,
        check=True,
    )
    metadata = json.loads((output / "post.json").read_text(encoding="utf-8"))
    body = (output / "post.html").read_text(encoding="utf-8")

    if not Path(EDGE_BINARY).is_file():
        sys.exit(f"Microsoft Edge is not installed at {EDGE_BINARY}")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    options = webdriver.EdgeOptions()
    options.binary_location = EDGE_BINARY
    # Chromium blocks DevTools access to its default profile. A separate,
    # persistent profile keeps the Patreon sign-in without weakening Edge.
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    try:
        driver = webdriver.Edge(options=options)
    except Exception as error:
        sys.exit(f"Could not launch Edge with its Patreon profile. Details: {error}")

    driver.get(CREATOR_URL)
    print(f"Opened Patreon: {driver.title} ({driver.current_url})")
    failed_control = "Create post button"
    try:
        # The creator UI opens a menu from this stable data attribute. The
        # Post item is rendered only after opening that menu.
        create = first_visible(driver, [
            (By.CSS_SELECTOR, "button[data-tag='create-content-button'][aria-label='Create post']"),
            (By.CSS_SELECTOR, "button[data-tag='create-content-button']"),
        ])
        driver.execute_script("arguments[0].click();", create)
        failed_control = "Post menu item"
        click_visible(driver, (By.XPATH, "//*[normalize-space()='Post']"))
    except RuntimeError:
        screenshot = Path("/tmp/patreon-selenium-state.png")
        driver.save_screenshot(str(screenshot))
        raise RuntimeError(
            f"Could not find Patreon’s {failed_control} after {WAIT_SECONDS} seconds. "
            f"Screenshot: {screenshot}; "
            f"page: {driver.title} ({driver.current_url})"
        ) from None
    title = first_visible(driver, [
        (By.CSS_SELECTOR, "input[name='title']"),
        (By.CSS_SELECTOR, "input[placeholder*='title' i]"),
        (By.XPATH, "//input[@type='text']"),
    ])
    set_text(driver, title, metadata["title"], "title")
    editor = first_visible(driver, [
        (By.CSS_SELECTOR, "[contenteditable='true'][role='textbox']"),
        (By.CSS_SELECTOR, "[contenteditable='true']"),
    ])
    set_editor_html(driver, editor, body)
    add_tags(driver, metadata["tags"])
    select_free_audience(driver)
    set_publish_date(driver, metadata["date"])

    if not args.publish:
        print("Draft filled and verified. Review it in Edge; rerun with --publish only when ready.")
        return

    publish = click_visible(driver, (By.XPATH, "//*[self::button or @role='button'][normalize-space()='Publish']"))
    if "publish" not in publish.text.lower():
        raise RuntimeError("Publish control could not be confirmed")
    print("Publish clicked. Confirm the post appears on the creator page before retrying this command.")


if __name__ == "__main__":
    main()
