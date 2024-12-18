from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import json

# Define constants
AMAZON_LOGIN_URL = "https://www.amazon.in/ap/signin"
BEST_SELLERS_URL = "https://www.amazon.in/gp/bestsellers/?ref_=nav_em_cs_bestsellers_0_1_1_2"

# Selenium WebDriver setup
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

# Amazon Login
def amazon_login(driver, email, password):
    driver.get(AMAZON_LOGIN_URL)
    try:
        # Enter email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        )
        email_input.send_keys(email)
        driver.find_element(By.ID, "continue").click()

        # Enter password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        )
        password_input.send_keys(password)
        driver.find_element(By.ID, "signInSubmit").click()

        # Verify successful login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "nav-link-accountList"))
        )
        print("Login successful")
    except TimeoutException:
        print("Login failed. Please check credentials or try again.")
        driver.quit()

# Scrape Best Sellers

def scrape_best_sellers(driver, categories_urls, output_file):
    scraped_data = []

    for category_url in categories_urls:
        driver.get(category_url)
        category_name = driver.find_element(By.CSS_SELECTOR, "span.zg_selected").text
        print(f"Scraping category: {category_name}")

        for _ in range(15):  # Loop to cover 1500 products (100 per page)
            products = driver.find_elements(By.CSS_SELECTOR, "div.zg-grid-general-faceout")
            for product in products:
                try:
                    product_name = product.find_element(By.CSS_SELECTOR, "a.a-link-normal").text
                    product_price = product.find_element(By.CSS_SELECTOR, "span.p13n-sc-price").text
                    discount = product.find_element(By.CSS_SELECTOR, "span.a-size-small").text if "off" in product.text else "N/A"
                    rating = product.find_element(By.CSS_SELECTOR, "span.a-icon-alt").text
                    product_url = product.find_element(By.CSS_SELECTOR, "a.a-link-normal").get_attribute("href")

                    # Navigate to product details page for additional info
                    driver.execute_script("window.open(arguments[0]);", product_url)
                    driver.switch_to.window(driver.window_handles[-1])

                    try:
                        ship_from = driver.find_element(By.CSS_SELECTOR, "div#tabular-buybox a.a-link-normal").text
                        sold_by = driver.find_element(By.CSS_SELECTOR, "div#merchant-info").text
                        product_description = driver.find_element(By.ID, "productDescription").text
                        images = [img.get_attribute("src") for img in driver.find_elements(By.CSS_SELECTOR, "img.a-dynamic-image")]
                        number_bought = driver.find_element(By.CSS_SELECTOR, "span#number-bought").text if driver.find_elements(By.CSS_SELECTOR, "span#number-bought") else "N/A"
                    except NoSuchElementException:
                        ship_from = sold_by = product_description = number_bought = "N/A"
                        images = []

                    scraped_data.append({
                        "Category": category_name,
                        "Product Name": product_name,
                        "Price": product_price,
                        "Discount": discount,
                        "Rating": rating,
                        "Ship From": ship_from,
                        "Sold By": sold_by,
                        "Description": product_description,
                        "Number Bought": number_bought,
                        "Images": images,
                    })

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except NoSuchElementException as e:
                    print(f"Error scraping product: {e}")

            # Navigate to next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
                next_button.click()
                time.sleep(2)
            except NoSuchElementException:
                break

    # Save data to file
    with open(output_file, "w", encoding="utf-8") as f:
        if output_file.endswith(".json"):
            json.dump(scraped_data, f, indent=4, ensure_ascii=False)
        else:
            writer = csv.DictWriter(f, fieldnames=scraped_data[0].keys())
            writer.writeheader()
            writer.writerows(scraped_data)

    print(f"Data saved to {output_file}")

# Main function
def main():
    email = input("Enter Amazon email: ")
    password = input("Enter Amazon password: ")
    categories_urls = [
        "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
        "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
        "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
        "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
        # Add more category URLs as needed
    ]
    output_file = "amazon_best_sellers.json"  # Change to .csv for CSV output

    driver = setup_driver()
    amazon_login(driver, email, password)
    scrape_best_sellers(driver, categories_urls, output_file)
    driver.quit()

if __name__ == "__main__":
    main()
