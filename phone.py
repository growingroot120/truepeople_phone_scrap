import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import re 
def normalize_phone_number(phone_number):
    return re.sub(r'\D', '', phone_number)

def scrape_data(driver, writer, formatted_phone_number):
    try:
        # Check if the required class 'card card-body shadow-form card-summary pt-3' is present
        card_elements = driver.find_elements(By.CSS_SELECTOR, '.card.card-body.shadow-form.card-summary.pt-3')
        if not card_elements:
            print("No 'card card-body shadow-form card-summary pt-3' class found. Skipping...")
            return  # Skip this phone number

        # If the class is found, click the div
        card_elements[0].click()
        
        # Scraping name
        name = driver.find_element(By.CLASS_NAME, 'oh1').text if driver.find_element(By.CLASS_NAME, 'oh1') else 'N/A'
        
        # Find the span containing age and date of birth information
        age_and_dob_elements = driver.find_elements("css selector", 'span')
        age_and_dob = next((el.text for el in age_and_dob_elements if "Age" in el.text or "Born" in el.text), 'N/A')
        
        street_address = driver.find_element("css selector", 'span[itemprop="streetAddress"]').text if driver.find_elements("css selector", 'span[itemprop="streetAddress"]') else 'N/A'
        locality = driver.find_element("css selector", 'span[itemprop="addressLocality"]').text if driver.find_elements("css selector", 'span[itemprop="addressLocality"]') else 'N/A'
        region = driver.find_element("css selector", 'span[itemprop="addressRegion"]').text if driver.find_elements("css selector", 'span[itemprop="addressRegion"]') else 'N/A'
        postal_code = driver.find_element("css selector", 'span[itemprop="postalCode"]').text if driver.find_elements("css selector", 'span[itemprop="postalCode"]') else 'N/A'

        # Initialize lists to store phone details
        phone_numbers, line_types, carriers = [], [], []
        
        # Select phone elements excluding the first two
        phone_elements = driver.find_elements("css selector", 'span[itemprop="telephone"]')  # Exclude first two phone numbers

        # Extract details from the first phone element only
        if phone_elements:  # Ensure there is at least one phone element
            first_phone_number = phone_elements[0].text.strip()  # Get the first phone number
            print(first_phone_number)
            # Normalize the phone numbers
            normalized_first_phone_number = normalize_phone_number(first_phone_number)
            normalized_formatted_phone_number = normalize_phone_number(formatted_phone_number)

            # Check if the first phone number matches the formatted_phone_number
            if normalized_first_phone_number == normalized_formatted_phone_number:
                phone_numbers.append(first_phone_number)
            else:
                print(f"First phone number {first_phone_number} does not match the searched number {formatted_phone_number}. Skipping...")
                return
        else:
            print("No phone numbers found on the page.")
        # Locate the parent div with classes 'row pl-sm-2 mt-2'
        parent_div = driver.find_element(By.CSS_SELECTOR, 'div.row.pl-sm-2.mt-2')

        # Find all child divs with classes 'col-6 col-md-3 mb-2' within the parent div
        home_value_divs = parent_div.find_elements(By.CSS_SELECTOR, 'div.col-6.col-md-3.mb-2')

        # List to store all <b> tag elements
        b_tags = []

        # Collect all <b> tags from the found div elements
        for div in home_value_divs:
            b_tag = div.find_element(By.TAG_NAME, 'b')
            b_tags.append(b_tag)

        # Check if there are at least 10 <b> tags
        if len(b_tags) >= 10:
            # Check if the 10th <b> tag value is "Individual"
            if b_tags[9].text.strip() == "Individual":
                # Save the 5th <b> tag value as home_price
                home_price = b_tags[4].text.strip()
                print(f"Home Price: {home_price}")
            else:
                print("The 10th <b> tag value is not 'Individual'.")
                return
        else:
            print("Not enough <b> tags found.")

        # Scraping email addresses
        email_elements = driver.find_elements("css selector", '.row.pl-sm-2 div.col')
        email_addresses = [email.text.strip() for email in email_elements if '@' in email.text]

        # Prepare data for CSV writing
        data = [name, age_and_dob, street_address, locality, region, postal_code, home_price, "; ".join(email_addresses)]
        writer.writerow(data)
        print(f"Data scraped and written to CSV for URL: {formatted_phone_number}")

    except Exception as e:
        print(f"Error occurred while scraping data: {e}")
def main():
    # Load phone numbers from CSV
    df = pd.read_csv("100.csv")
    phone_numbers = df['Phone Number'].tolist()

    # Set up Chrome browser
    service = Service(ChromeDriverManager().install())
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-fullscreen")  # Open browser in full screen mode
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # CSV file setup
        with open('scraped_data.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Age and DOB', 'Street Address', 'Locality', 'Region', 'Postal Code', 'Home Price', 'Email Addresses'])

            # Open the search page once
            url = "https://www.truepeoplesearch.com/"

            for phone_number in phone_numbers:
                driver.get(url)
                time.sleep(2)  # Wait for the page to load fully

                # Click on the phone number search tab once
                phone_search_tab = driver.find_element(By.ID, "searchTypePhone-d")
                phone_search_tab.click()
                time.sleep(1)                
                # Convert to string to ensure it's subscriptable
                phone_number_str = str(phone_number)

                # Check if the number starts with '1' and has 11 digits (standard US format including country code)
                if phone_number_str.startswith('1') and len(phone_number_str) == 11:
                    phone_number_str = phone_number_str[1:]  # Remove the leading '1'

                # Format the phone number from '6195307973' to '(619) 530 7973'
                formatted_phone_number = f"({phone_number_str[:3]}) {phone_number_str[3:6]} {phone_number_str[6:]}"

                # Clear the previous phone number and enter the new, formatted one
                phone_input = driver.find_element(By.NAME, "PhoneNo")
                phone_input.clear()
                phone_input.send_keys(formatted_phone_number)
                print(formatted_phone_number)  # Print the formatted phone number
                phone_input.send_keys(Keys.RETURN)
                scrape_data(driver, writer, formatted_phone_number)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the browser at the end
        driver.quit()
        print("Chrome browser closed.")

if __name__ == "__main__":
    main()
