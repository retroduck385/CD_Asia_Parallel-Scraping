
from utils.driver_setup import initialize_driver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

CASE_CONFIG = {

    ## Adjust the Config Accrodingly 
    "libraryItemNo": 3,
    "libraryName": "Taxation",
    "contents": [
        {
            "contentItemNo": "1",
            "contentTitle": "Bureau of Internal Revenue (BIR)",
            "subContents": [
                {
                    "subcontentItemNo": "8",
                    "subcontentTitle": "Regional Revenue Memorandum Circular",
                    "case": [
                               
                    ]
                }
            ]
        }
    ]
}

## 1. GO TO LOGIN PAGE WEBDRIVER WAIT UNTIL FIELDS ARE PRESENT AND FILL IN CREDENTIALS
## 2. INPUT CREDENTIALS AND CLICK LOGIN 
##  2.1 Check if there is a sign-in alert and click continue else continue
# 3. Go to the HOMEPAGE, Check if the with WebDriver wait if the main page is loaded.


def collect_row_metadata(driver: WebDriver) -> list[int]:
    """
    Return a list of row indexes to be used for parallel scraping.
    """
    fetch_table(driver)
    rows = fetch_table_rows(driver)
    rows_list = list(range(len(rows)))
    print (f"[ROWS LIST]: {rows_list}")
    return rows_list  # e.g. [0, 1, 2, ...]


def wait_for_backdrop_to_disappear(driver: WebDriver) -> None:
    try:
        wait_for_backdrop_to_disappear(driver)
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "MuiBackdrop-root"))
        )
        print("[✅STATUS] Backdrop has disappeared.")
    except:
        print("[⚠️WARNING] Backdrop did not disappear in time.")

### Get the number of documents to scrape in the subgroup, returns int
def get_number_of_documents(driver: WebDriver) -> int:
    try:
        # Wait for the element that contains the number of documents
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, "/html/body/div/main/div/div/div/div/div/div/div[1]/div[1]/span"
            ))
        )

        # Wait until the text becomes a valid number        
        for _ in range(10):  # Retry up to 10 times (~10s)
            text = element.text.strip()
            if text and not text.lower().startswith("searching"):
                try:
                    number = int(text.split()[0])  # e.g., "123 Documents"
                    print(f"[✅STATUS] Found {number} documents.")
                    return number
                except ValueError:
                    pass
            time.sleep(1)

        raise Exception("Timed out waiting for valid document count text.")

    except Exception as e:
        print(f"[❌STATUS] Error getting number of documents: {e}")
        return 0


def navigate_to_next_page(driver: WebDriver) -> None:
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/main/div/div/div/div/div/div/div[1]/div[2]/nav/ul/li[7]/button"))
        )

        if "Mui-disabled" in next_button.get_attribute("class"):
            print("[ℹ️STATUS] Reached last page. No more pages to scrape.")


        # Scroll and wait a bit
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(0.5)

        try:
            next_button.click()
        except Exception as e:
            print("[⚠️FALLBACK] Regular click failed, trying JS click.")
            driver.execute_script("arguments[0].click();", next_button)

        print("[🔁STATUS] Navigated to next page.")

        # Wait for new table to load
        time.sleep(2)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )
   
    except Exception as e:
        print(f"[❌STATUS] Error navigating to next page: {e}")


    

def get_rows_in_page(driver: WebDriver) -> int:
    try:

        # Get all rows in the table
        rows = driver.find_elements(By.XPATH, "//table//tbody/tr")
        print(f"[✅STATUS] Found {len(rows)} rows in the table of the current page.")
        return len(rows)

    except Exception as e:
        print(f"[❌STATUS] Error getting rows in the current page: {e}")
        return 0
    

def is_document_equal_row_scraped(current_row_scrape: int, documents_to_scrape: int) -> bool:
    """
    Check if the current row scraped is equal to the total number of documents to scrape.
    """
    return current_row_scrape == documents_to_scrape



def extract_row_case(driver: WebDriver, total_row_scraped: int) -> None:
    
    date = get_doc_date(driver)
    reference_number = get_ref_number(driver)
    subject = get_subject(driver)
    to_info = get_to_info(driver)
    url = get_url(driver)
    details = get_details(driver)
    cited_reference = get_cited_reference(driver)
    display_document_info(driver, date, reference_number, subject, to_info, url, cited_reference, details)
    append_data_info(driver, date, reference_number, subject, to_info, url, cited_reference, details, total_row_scraped)

def append_data_info(driver: WebDriver, date: str, ref_number: str, subject_info: str, to_info: str, url: str, cited_reference: dict, details: dict, total_row_scraped: int) -> None:
    regulation_entry = {
        "regulationNo": f"{total_row_scraped}"
    }

    regulation_entry["Original Law"] = {
        "Date": date,
        "Reference Number": ref_number,
        "Subject": subject_info,
        "To": to_info,
        "URL": url,
        "Details": details
    }

    if cited_reference:
        regulation_entry["Cited Reference"] = cited_reference

    CASE_CONFIG["contents"][0]["subContents"][0]["case"].append(regulation_entry)

def get_cited_reference(driver: WebDriver) -> dict[str, list[dict[str, str]]]:
    cited_reference = {}

    try:
        # Wait for the cited reference table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#document-container > div"))
        )
        print(f"[✅ STATUS] Cited Reference Table Loaded")

        try:
            container = driver.find_element(By.CSS_SELECTOR, "#document-container > div")
            print(f"[✅ STATUS] Cited Reference Table Contents Loaded")
        except Exception as e:
            print(f"[❌ ERROR] Failed to locate the table container: {e}")
            return cited_reference

        try:
            references = get_cited_reference_header(driver)
        except Exception as e:
            print(f"[❌ ERROR] Failed to get reference headers: {e}")
            return cited_reference

        if references:
            for reference in references:
                try:
                    # Locate the dropdown button
                    dropdown = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, f"//button[.//h2[text()='{reference}']]"))
                    )

                    # Check if already expanded
                    is_expanded = dropdown.get_attribute("aria-expanded") == "true"

                    if not is_expanded:
                        WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, f"//button[.//h2[text()='{reference}']]"))
                        ).click()
                        time.sleep(2)

                    # Scroll the container to load all rows
                    last_height = 0
                    scroll_attempts = 0
                    max_scrolls = 10

                    while scroll_attempts < max_scrolls:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
                        time.sleep(1)
                        new_height = driver.execute_script("return arguments[0].scrollTop", container)

                        if new_height == last_height:
                            break

                        last_height = new_height
                        scroll_attempts += 1

                    # Scrape the rows
                    rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root table-row-even mui-2u4x71']/tr")
                    reference_entries = []

                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 3:
                            reference_entry = {
                                "Reference Number": cols[0].text.strip(),
                                "Title": cols[1].text.strip(),
                                "Date": cols[2].text.strip()
                            }
                            reference_entries.append(reference_entry)

                    cited_reference[reference] = reference_entries

                except Exception as e:
                    print(f"[❌ ERROR] Failed to process reference '{reference}': {e}")
        else:
            print("[⚠️ WARNING] No references found")

    except Exception as e:
        print(f"[❌ CRITICAL ERROR] Failed to load cited references section: {e}")

    return cited_reference

def get_cited_reference_header(driver: WebDriver) -> list:

    headers = []

    ## Get h2 elements for the title of the Cited Reference
    try:
        h2_elements  = driver.find_elements(By.XPATH, "//h2[contains(@class, 'MuiTypography-h2')]")

        ## If there is a h2 element append it in headers list
        if h2_elements:
            for elem in h2_elements:
                headers.append(elem.text)
            
            return headers
        ## Else just return an empty headers list
        else:
            return headers
        
    except Exception as e:
        print(f"[❌ UNEXPECTED ERROR] {e}")
        return None

def get_url(driver: WebDriver) -> str:

    ## Gets the URL
    url = driver.current_url
    return url

def get_details(driver:WebDriver) -> dict: 

    retries = 3
    for attempt in range(retries):
        try:            
            tab_panel = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[starts-with(@id, 'simple-tabpanel-') and not(@hidden)]")))
            
            print(f"[✅ STATUS] Content Panel Loaded on Attempt {attempt + 1}")
            
            # Get the text inside the panel
            try:
                all_p_tags = tab_panel.find_elements(By.XPATH, ".//p")
            except Exception as e:
                print(f"[❌ ERROR] Failed to extract <p> tags: {e}")
                continue

            details = []
            footnotes = []
            annex_sections = {}
            curr_annex = None

            for p in all_p_tags:
                    p_class = p.get_attribute("class")
                    text = p.text.strip()
                    links = p.find_elements(By.TAG_NAME, "a") 

                    if not text:
                        continue
                    if p_class == "footnote-area":
                        footnotes.append(p.text.strip())
                    elif text.startswith("ANNEX"):
                        curr_annex = text
                        annex_sections[curr_annex] = {"details": [], "links": []}
                    elif curr_annex:
                        annex_sections[curr_annex]["details"].append(text)
                        for link in links:
                            href = link.get_attribute("href")
                            annex_sections[curr_annex]["links"].append(href)
                    else:
                        details.append(p.text.strip())
            
            # Clean out any empty text entries
            filtered_details = []
            for line in details:
                if line:  
                    filtered_details.append(line)
            details = filtered_details
                
            filtered_footnotes = []
            for line in footnotes:
                if line:  
                    filtered_footnotes.append(line)
            footnotes = filtered_footnotes

            for annex, lines in annex_sections.items():
                filtered_lines = []
                for line in lines["details"]:
                    if line.strip():  
                        filtered_lines.append(line)
                annex_sections[annex]["details"] = "\n\n".join(filtered_lines)


            details = {
                "Details": "\n\n".join(details[2:]),
                "Footnote": "\n\n".join(footnotes) if footnotes else "No footnotes found",
                "Annexes": annex_sections if annex_sections else "No annexes found"
            }

            return details
        
        except Exception as e:
            print(f"[❌ ERROR] Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  

    print(f"[❌ ERROR] Giving up after {retries} failed attempts.")
    return None

def get_ref_number (driver: WebDriver) -> str:
    try:
        # Wait for the element that contains the regulation number
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#reference_no > span"))
        )
        reg_no = element.text.strip()
        print(f"[✅STATUS] Found Regulation Number: {reg_no}")
        return reg_no
    except Exception as e:
        print(f"[⚠️FALLBACK TRIGGERED] Trying Fallback:")        
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#document-container > p:nth-child(3)"))
        )
        reg_no = element.text.strip()
        print(f"[✅STATUS] Found Regulation Number: {reg_no}")
        return reg_no
    except Exception as e:
        print(f"[❌STATUS] Error getting Regulation Number: {e}")
        return None

def display_document_info(driver: WebDriver, date: str, ref_number: str, subject_info: str, to_info: str, url: str, cited_reference: dict, details: dict) -> None:
    print("\n [ℹ️STATUS] Displaying Document Information:")
    print("\t ================INFO================ \n ")
    print(f"\t[ℹ️ Date]: {date if date else None}")
    print(f"\t[ℹ️ Ref Number]: {ref_number if ref_number else None}")
    print(f"\t[ℹ️ URL]: {url if url else None}")
    if subject_info:
        print(f"\t[ℹ️ Subject]: {subject_info}")
        if to_info:
            print(f"\t[ℹ️ To]: {to_info}")
        else:
            print("\t[ℹ️ To]: Not available for this document.")
    else:
        print("\t[ℹ️ Subject]: Not available for this document.")
        print("\t[ℹ️ To]: Not available for this document.")
    print(f"\t[ℹ️ Details]: {details if details else None}...")  # Display first 100 characters of details
    print(f"\t[ℹ️ Cited Reference]: {cited_reference if cited_reference else None}...")
    print("\t ================INFO================ \n ")

def get_doc_date (driver: WebDriver) -> str:
    try:
        # Wait for the element that contains the regulation date
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#document-container > p:nth-child(2)"))
        )
        doc_date = element.text.strip()
        print(f"[✅STATUS] Found Document Date: {doc_date}")
        return doc_date
    except Exception as e:
        print(f"[❌STATUS] Error getting Document Date: {e}")
        return None
    
def get_to_info (driver: WebDriver) -> str:
    try:
        # Wait for the first <tr> to be present
        trow = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#document-container > div:nth-child(4) > table > tbody > tr:nth-child(3)"))
        )
        td_elements = trow.find_elements(By.TAG_NAME, "td")
        to_info_parts = [td.text.strip() for td in td_elements[2:]]
        to_info = " ".join(to_info_parts)
        print(f"[✅STATUS] Found TO Info: {to_info}")
        return to_info
    except Exception as e:
        print(f"[❌STATUS] The TO Info is not available for the document")
        return None
    
## IF THERE IS SUBJECT, THERE IS ALSO TO INFO
def get_subject(driver: WebDriver) -> str:
    try:
        # Wait for the first <tr> to be present
        trow = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#document-container > div:nth-child(4) > table > tbody > tr:nth-child(1)"))
        )

        # Get all <td> elements inside the row
        td_elements = trow.find_elements(By.TAG_NAME, "td")

        if len(td_elements) <= 2:
            print("[⚠️STATUS] Index is less than or equal to 2.")
            print("⚠️STATUS] Subject is not available for the document.")
            return None

        # Get the text of <td>s from index 2 and onward
        subject_parts = [td.text.strip() for td in td_elements[2:]]
        subject = " ".join(subject_parts)  # Join with space, change separator if needed

        print(f"[✅STATUS] Found Subject: {subject}")
        return subject
    except Exception as e:
        print(f"[❌STATUS] Error getting Subject: {e}")
        return None
    

def fetch_table(driver: WebDriver) -> WebElement:
    table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table"))
            )
    print("[✅STATUS] Table found.")
    return table 


def fetch_table_rows(driver: WebDriver) -> WebElement:
    table = fetch_table(driver)
    rows = table.find_elements(By.XPATH, ".//tbody/tr")
    print(f"[✅STATUS] Found {len(rows)} rows in the table.")
    return rows 


def click_elements_per_row(driver: WebDriver, total_row_scraped: int, page_number: int, documents_to_scrape: int) -> int:
    print(f"[✅STATUS] Scraping Page: {page_number}.")
    rows = fetch_table_rows(driver)  
    rows_scraped_this_page = 0       

    for row in rows:
        if total_row_scraped >= documents_to_scrape:  
            break

        try:
            original_window = driver.current_window_handle
            print(f'[✅STATUS] Scraping row {total_row_scraped + 1} of {documents_to_scrape} documents...')

            element = row.find_element(By.TAG_NAME, "td")
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", element)

            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            new_window = [window for window in driver.window_handles if window != original_window][0]
            driver.switch_to.window(new_window)

            try:
                extract_row_case(driver, total_row_scraped + 1)
            except Exception as e:
                print(e)
            finally:
                driver.close()
                driver.switch_to.window(original_window)

            total_row_scraped += 1
            rows_scraped_this_page += 1 

        except Exception as e:
            print(e)

    return rows_scraped_this_page  


## Used to paginate X amount of time in the Subcontent Page 
def initial_pagination(driver: WebDriver, pages_to_advance: int ) -> int:

    ## The page -1
    for _ in range (pages_to_advance):
        try:
            WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
        except Exception as e:
            print(f"Failed to click 'Next Page' button: {e}")
            break

    time.sleep(1)
    return (pages_to_advance) * 20

def get_page_number (scraped_amt: int) -> int:
    
    return int(scraped_amt / 20)

def handle_table(driver: WebDriver) -> None:

    ## Change this to the amount you want to jump to
    # scraped_documents = initial_pagination(driver, get_page_number(1480))
    # documents_to_scrape = get_number_of_documents(driver)
    # current_row_scraped = 0
    # total_row_scraped = scraped_documents
    # page_number = scraped_documents + 1

    #Bring this back if start from start
    documents_to_scrape = get_number_of_documents(driver) 
    current_row_scraped = 0
    total_row_scraped = 0
    page_number = 1

    max_rows_per_page = 20 ## adjust this later in the config 

    while total_row_scraped != documents_to_scrape:
        rows_scraped_this_page = click_elements_per_row(driver, total_row_scraped, page_number, documents_to_scrape)

        current_row_scraped += rows_scraped_this_page
        total_row_scraped += rows_scraped_this_page
        page_number += 1
         
        if current_row_scraped >= max_rows_per_page: 
            navigate_to_next_page(driver)
            print("[🔁Next Page] Navigated to the next page.") 
            current_row_scraped = 0 
            
        if total_row_scraped >= documents_to_scrape:
            break

## e.g From Taxation -> BIR ->  BIR Citizen CHarter, Memorada, Primer, Revenue Memorandum Orders ... etc
def click_content_subgroup(driver: WebDriver, content_subgrup: str) -> None:
    time.sleep(5)
    try:
        # Wait for the content group to be clickable and then click it
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body > div > main > div > div > div > div > div > ul")))
        # time.sleep(0.5)  # Let the page stabilize
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, content_subgrup))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        # time.sleep(0.5)
        element.click()
        print(f"[✅STATUS] Clicked on content subgroup with CSS Selector: {content_subgrup}")
        # time.sleep(10)  # Wait for the content to load
    except Exception as e:
        print(f"[❌STATUS] Error clicking content subgroup: Page did not load or slow connection. Retry Again ! or See Exception: {e}")


## Open Contents of the Filtered Item (e.g From Taxation -> BIR Directories, BIR Forms, Rulings etc .)
def click_contents_item(driver: WebDriver, content_item_selector: str) -> None:
    try:
        # Wait for the item to be clickable and then click it
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, content_item_selector))
        ).click()
        print(f"[✅STATUS] Clicked on content item with CSS Selector: {content_item_selector}")
        # time.sleep(10)  # Wait for the content to load
    except Exception as e:
        print(f"[❌STATUS] Error clicking content item: {e}")   


## 1. Clicks the library dropdown
def click_library_tabs(driver: WebDriver) -> bool:
    try:
        # Wait for the element to be present
        library_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="library-menu-button"]'))
        )

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", library_button)
        time.sleep(0.3)

        try:
            # Attempt native click
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="library-menu-button"]'))
            ).click()
            time.sleep(0.5)  # Let the dropdown stabilize
            print("[✅STATUS] Clicked on Libraries dropdown (native click).")
        except Exception as click_error:
            # Fallback to JS click
            driver.execute_script("arguments[0].click();", library_button)
            print("[⚠️FALLBACK] Clicked on Libraries dropdown (JS click).")

        # Confirm dropdown opened by waiting for the menu to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//ul[contains(@class,'MuiList-root')]"))
        )
        print("[✅STATUS] Libraries dropdown content loaded.")
        return True

    except Exception as e:
        print(f"[❌STATUS] Error clicking Libraries dropdown: {e}")
        return False

    

## Select an Items in the Libraries Dropdown [taxation, jurisprudence, etc.]
def click_item_button_in_library_tabs(driver: WebDriver, item_xpath: str) -> None:
    try:

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, item_xpath))).click()
        print(f"[✅STATUS] Clicked on item button with XPath: {item_xpath}")
        # time.sleep(2)  # Wait for the item to be selected


        #Click a neutral part of the page to close the dropdown
        print("[✅STATUS] Clicking a neutral part of the page to close the dropdown.")
        body_element = driver.find_element(By.TAG_NAME, "body")
        body_element.click()

    except Exception as e:
        print(f"[❌STATUS] Error clicking Item button XPath {item_xpath}: {e}")

    

def sign_in_alert_present(driver: WebDriver) -> bool:
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
        )
        return True
    except:
        print("[❌STATUS] No sign-in alert shown.")
        return False
        
def fill_login_field(driver: WebDriver) -> None:
# Fill credentials
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "body > div"))
    )
    print("🔑 Filling in login credentials")
    input_element = driver.find_element(By.ID, "user-id")
    input_element.clear()
    input_element.send_keys(f"{email}")
    input_element = driver.find_element(By.ID, "user-password")
    input_element.clear()
    input_element.send_keys(f"{password}" + Keys.ENTER)

    if sign_in_alert_present(driver):
        
    # Step 1.5: Handle Sign-in Alert
        try:
            driver.find_element(By.XPATH, '//button[contains(text(), "Continue")]').click()
            print("[✅STATUS] Handled sign-in alert.")
        except:
            print("[❌STATUS] No sign-in alert shown.")
    


def scrape(driver: WebDriver, base_url: str, item_xpath: str, content_group: str, content_subgroup) -> None:
    print("🔍 Navigating to CDAsia Online")
    driver.get(base_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "body > div > main"))
    )   
    print("✅ Successfully navigated to CDAsia Online")
    fill_login_field(driver)


    if click_library_tabs(driver):
        click_item_button_in_library_tabs(driver, item_xpath)
        click_contents_item (driver, content_group)
        click_content_subgroup(driver, content_subgroup)
        handle_table(driver)

        
        
    else:
        print(f"[❌STATUS] Failed to click Libraries dropdown, cannot proceed to XPath: {item_xpath}  button.")



def main():
    print("🚀 Starting CDAsia Scraper")
    start_time = time.time()
    driver = initialize_driver()
    print(f'[STATUS CHECK IN MAIN]{driver.capabilities}')
    base_url = "https://cdasiaonline.com/"
    ## Taxation Law dropdown item, change this xpath item if will scrape other items
    item_xpath = "//span[contains(text(), 'Taxation')]/ancestor::label"

    ## CSS Selector for the content group to click
    ## Bureau of Internal Revenue (BIR)
    content_group_xpath = '/html/body/div/main/div/div/div/div/div/ul/li[3]/button/div[1]/span'

    ## CSS Selector for the subgroup of the content group/content item to click
    ## Revenue Memorandum Orders
    # content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(14) > button > div.MuiListItemText-root.mui-khtx2o > span"

    ## Revenue Audit Memorandum Orders
    # content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(10) > button > div.MuiListItemText-root.mui-khtx2o > span"

    ## Joint Issuances
    # content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(5) > button > div.MuiListItemText-root.mui-khtx2o > span"

    ## Revenue Operations Memoranda
    # content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(16) > button > div.MuiListItemText-root.mui-khtx2o > span"

    ## Primer  
    # content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(7) > button > div.MuiListItemText-root.mui-khtx2o > span"

    ## Citizen’s Charter 
    # content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(1) > button > div.MuiListItemText-root.mui-khtx2o > span"

    ## Regional Revenue Memorandum Circular 
    content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(8) > button > div.MuiListItemText-root.mui-khtx2o > span"


    try:
        scrape(driver, base_url, item_xpath, content_group_xpath, content_subgroup_css_selector)
    except Exception as e:
        print(e)
    finally:
        print(json.dumps(CASE_CONFIG, indent=4, ensure_ascii=False))
        filename = "BIR_Regional_Revenue_Memorandum_Circular.json"
        with open(filename, 'w') as file:
            json.dump(CASE_CONFIG, file, indent=4)

        driver.quit()
        end_time = time.time()  # ⏱️ End timer
        elapsed = end_time - start_time
        mins, secs = divmod(elapsed, 60)
        print(f"\n⏱️ Scraping finished in {int(mins)} minute(s) and {int(secs)} second(s).")



if __name__ == "__main__":
    main()  

