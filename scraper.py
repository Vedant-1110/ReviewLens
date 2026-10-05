import os
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = "data/scraped_reviews.csv"

SEARCH_QUERY = "restaurants in Vadodara"
MAX_REVIEWS = 100

os.makedirs("data", exist_ok=True)
os.makedirs("debug", exist_ok=True)


# ============================================================
# OPEN GOOGLE MAPS
# ============================================================

def open_google_maps(driver, search_query):
    print("\nOpening Google Maps...")

    driver.get("https://www.google.com/maps")

    # Wait for the page to load
    time.sleep(5)

    print("Google Maps opened.")
    print("Looking for search box...")

    search_box = None

    selectors = [
        (By.ID, "searchboxinput"),
        (By.CSS_SELECTOR, "input[aria-label='Search Google Maps']"),
        (By.CSS_SELECTOR, "input[aria-label*='Search']"),
        (By.CSS_SELECTOR, "input[placeholder*='Search']"),
        (By.CSS_SELECTOR, "input[role='combobox']"),
    ]

    for by, value in selectors:
        try:
            elements = driver.find_elements(by, value)

            print(
                f"Trying {by} = {value} "
                f"-> found {len(elements)}"
            )

            for element in elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        search_box = element
                        break
                except Exception:
                    continue

            if search_box:
                break

        except Exception as e:
            print(f"Selector failed: {e}")

    if search_box is None:
        print("\nCould not find Google Maps search box.")
        print("Current URL:", driver.current_url)

        # Save page source for debugging
        with open(
            "debug/google_maps_page.html",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(driver.page_source)

        raise Exception(
            "Google Maps search box not found."
        )

    print("✅ Search box found.")

    search_box.click()
    search_box.clear()
    search_box.send_keys(search_query)

    print(f"Searching for: {search_query}")

    search_box.send_keys(Keys.ENTER)

    time.sleep(7)

    print("✅ Search submitted.")
    print("Current URL:", driver.current_url)
# ============================================================
# FIND FIRST RESTAURANT
# ============================================================

def open_first_restaurant(driver):

    print("\nFinding restaurant...")

    selectors = [
        "a[href*='/maps/place/']",
        "div[role='article'] a[href*='/maps/place/']"
    ]

    restaurant = None

    for selector in selectors:

        try:

            WebDriverWait(
                driver,
                10
            ).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selector)
                )
            )

            restaurants = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            if restaurants:

                restaurant = restaurants[0]
                break

        except TimeoutException:
            continue

    if restaurant is None:
        raise Exception(
            "No restaurant result was found."
        )

    try:

        name = restaurant.text.strip()

    except Exception:

        name = "Unknown Restaurant"

    print(f"Opening: {name}")

    driver.execute_script(
        "arguments[0].click();",
        restaurant
    )

    time.sleep(5)

    return name


# ============================================================
# OPEN REVIEWS
# ============================================================
def open_reviews(driver):
    print("\nFinding Reviews button...")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@aria-label, 'Reviews')]")
            )
        )
    except TimeoutException:
        raise Exception("Reviews button was not found.")

    buttons = driver.find_elements(
        By.XPATH,
        "//button[contains(@aria-label, 'Reviews')]"
    )

    if not buttons:
        raise Exception("Reviews button was not found.")

    button = buttons[-1]

    driver.execute_script(
        "arguments[0].click();",
        button
    )

    print("Reviews button clicked.")

    # Give Google Maps time to open the reviews panel
    time.sleep(5)

    print("Waiting for reviews to load...")

    # Try to make the review cards appear
    for attempt in range(10):

        cards = driver.find_elements(
            By.CSS_SELECTOR,
            "[data-review-id]"
        )

        print(
            f"Review loading attempt "
            f"{attempt + 1}/10 | "
            f"Review cards: {len(cards)}"
        )

        if cards:
            print("✅ Review cards loaded.")
            return find_review_container(driver)

        # Scroll the page/panel a little to trigger loading
        try:
            driver.execute_script(
                "window.scrollBy(0, 500);"
            )
        except Exception:
            pass

        time.sleep(2)

    print("⚠️ Review cards did not appear.")

    return find_review_container(driver)
# ============================================================
# FIND REVIEW CONTAINER
# ============================================================

def find_review_container(driver):

    selectors = [
        "div[role='feed']",
        "div.m6QErb[aria-label]"
    ]

    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            for element in elements:

                try:

                    if element.find_elements(
                        By.CSS_SELECTOR,
                        "[data-review-id]"
                    ):

                        print("Review container found.")
                        return element

                except StaleElementReferenceException:

                    continue

        except Exception:

            continue

    print("⚠️ Review container not found.")

    return None


# ============================================================
# EXTRACT ONE REVIEW
# ============================================================

def extract_review(card):

    try:

        # Author
        try:

            author = card.find_element(
                By.CSS_SELECTOR,
                ".d4r55"
            ).text.strip()

        except NoSuchElementException:

            author = "Unknown"

        # Rating
        try:

            rating_element = card.find_element(
                By.CSS_SELECTOR,
                "span[role='img'][aria-label*='star']"
            )

            rating_text = rating_element.get_attribute(
                "aria-label"
            )

            rating = float(
                rating_text.split()[0]
            )

        except Exception:

            rating = None

        # Review text
        text = ""

        text_selectors = [
            ".wiI7pd",
            "span.wiI7pd"
        ]

        for selector in text_selectors:

            try:

                text_element = card.find_element(
                    By.CSS_SELECTOR,
                    selector
                )

                text = text_element.text.strip()

                if text:
                    break

            except NoSuchElementException:

                continue

        # Date
        try:

            date_element = card.find_element(
                By.CSS_SELECTOR,
                ".rsqaWe"
            )

            review_date = date_element.text.strip()

        except NoSuchElementException:

            review_date = ""

        if not author and not text:
            return None

        return {
            "author_name": author,
            "text": text,
            "rating": rating,
            "review_date": review_date
        }

    except StaleElementReferenceException:

        return None

    except Exception:

        return None


# ============================================================
# COLLECT REVIEWS
# ============================================================

def collect_reviews(
    driver,
    max_reviews=100
):

    print("\nStarting review collection...")

    reviews = []
    seen = set()

    no_new_data = 0

    for scroll_number in range(1, 31):

        time.sleep(3)

        cards = driver.find_elements(
            By.CSS_SELECTOR,
            "[data-review-id]"
        )

        print(
            f"Scroll {scroll_number:02d} | "
            f"Loaded review cards: {len(cards)} | "
            f"Collected: {len(reviews)}"
        )

        old_count = len(reviews)

        for card in cards:

            try:

                review = extract_review(card)

                if not review:
                    continue

                key = (
                    review["author_name"],
                    review["text"]
                )

                if key in seen:
                    continue

                seen.add(key)

                reviews.append(review)

                print(
                    f"\nReview #{len(reviews)}"
                )

                print(
                    f"Author: "
                    f"{review['author_name']}"
                )

                print(
                    f"Rating: "
                    f"{review['rating']}"
                )

                print(
                    f"Date: "
                    f"{review['review_date']}"
                )

                print(
                    f"Text: "
                    f"{review['text'][:120]}..."
                )

                if len(reviews) >= max_reviews:

                    print(
                        f"\n✅ Reached "
                        f"{max_reviews} reviews."
                    )

                    return reviews

            except StaleElementReferenceException:

                continue

        if len(reviews) == old_count:

            no_new_data += 1

        else:

            no_new_data = 0

        review_container = find_review_container(
            driver
        )

        if review_container is None:

            time.sleep(2)
            continue

        try:

            driver.execute_script(
                """
                arguments[0].scrollTop =
                arguments[0].scrollHeight;
                """,
                review_container
            )

        except StaleElementReferenceException:

            print(
                "⚠️ Review container changed. "
                "Retrying..."
            )

            continue

        if no_new_data >= 5:

            print(
                "\nNo new reviews are appearing."
            )

            break

    return reviews


# ============================================================
# SAVE REVIEWS
# ============================================================

def save_reviews(
    reviews,
    restaurant_name
):

    if not reviews:

        print(
            "\n⚠️ No reviews were collected."
        )

        return False

    rows = []

    for review in reviews:

        rows.append({
            "business_name": restaurant_name,
            "author_name": review["author_name"],
            "text": review["text"],
            "rating": review["rating"],
            "review_date": review["review_date"]
        })

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"\n✅ Saved {len(df)} reviews."
    )

    print(
        f"File: {OUTPUT_FILE}"
    )

    return True


# ============================================================
# MAIN SCRAPER FUNCTION
# ============================================================

def main(
    search_query=SEARCH_QUERY,
    max_reviews=MAX_REVIEWS
):

    print("\n")
    print("=" * 60)
    print("              REVIEWLENS SCRAPER")
    print("=" * 60)

    driver = webdriver.Chrome()

    driver.maximize_window()

    try:

        open_google_maps(
            driver,
            search_query
        )

        restaurant_name = (
            open_first_restaurant(driver)
        )

        review_container = open_reviews(
            driver
        )

        if review_container is None:

            raise Exception(
                "Could not locate review container."
            )

        reviews = collect_reviews(
            driver,
            max_reviews
        )

        save_reviews(
            reviews,
            restaurant_name
        )

        return reviews

    except Exception as e:

        print("\n")
        print("=" * 60)
        print("SCRAPER ERROR")
        print("=" * 60)

        print(e)

        return []

    finally:

        print(
            "\nClosing browser..."
        )

        driver.quit()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    main()