
from utils.driver_setup import initialize_driver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


import time


## 1. GO TO LOGIN PAGE WEBDRIVER WAIT UNTIL FIELDS ARE PRESENT AND FILL IN CREDENTIALS
## 2. INPUT CREDENTIALS AND CLICK LOGIN 
##  2.1 Check if there is a sign-in alert and click continue else continue
# 3. Go to the HOMEPAGE, Check if the with WebDriver wait if the main page is loaded.

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
            EC.presence_of_element_located((By.XPATH, "/html/body/div/main/div/div/div/div/div/div/div[1]/div[1]/span"))
        )
        # Extract the text and parse the number
        text = element.text
        number = int(text.split()[0])  # Assuming format like "123 Documents"
        print(f"[✅STATUS] Found {number} documents.")
        return number
    except Exception as e:
        print(f"[❌STATUS] Error getting number of documents: {e}")
        return 0


# def get_row_data() -> None:
#     # Placeholder function for row data extraction logic
#     pass


# def navigate_to_next_page(driver: WebDriver) -> None:
#     pass

def get_table_data(driver: WebDriver) -> None:
    documents_to_scrape = get_number_of_documents(driver)
    row_start = 1
    try:
        # Wait for the table to be present
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )
        print("[✅STATUS] Table found.")
        
        # Get all rows in the table body
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        print(f"[✅STATUS] Found {len(rows)} rows in the table.")
        
        # Extract data from each row
        data = []
        for row in rows:
            print(f"[STATUS] Scraping row {row_start} of {documents_to_scrape}")
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text for cell in cells]
            data.append(row_data)
            print(f"[✅STATUS] Row {row_start} data: {row_data}")
            row_start += 1


        
        return data
    except Exception as e:
        print(f"[❌STATUS] Error getting table data: {e}")
        return []

## e.g From Taxation -> BIR ->  BIR Citizen CHarter, Memorada, Primer, Revenue Memorandum Orders ... etc
def click_content_subgroup(driver: WebDriver, content_subgrup: str) -> None:
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
        print(f"[❌STATUS] Error clicking content subgroup: {e}")


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
    input_element.send_keys("accounting@onecfoph.co")
    input_element = driver.find_element(By.ID, "user-password")
    input_element.clear()
    input_element.send_keys("HU9W19pr" + Keys.ENTER)

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
        get_table_data(driver)

        
        
    else:
        print(f"[❌STATUS] Failed to click Libraries dropdown, cannot proceed to XPath: {item_xpath}  button.")


    # Step 3: Click the Item in Contents Page

    
        


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
    content_subgroup_css_selector = "body > div > main > div > div > div > div > div > ul > li:nth-child(14) > button > div.MuiListItemText-root.mui-khtx2o > span"
    
    try:
        scrape(driver, base_url, item_xpath, content_group_xpath, content_subgroup_css_selector)
    except Exception as e:
        print(e)
    finally:
        driver.quit()
        end_time = time.time()  # ⏱️ End timer
        elapsed = end_time - start_time
        mins, secs = divmod(elapsed, 60)
        print(f"\n⏱️ Scraping finished in {int(mins)} minute(s) and {int(secs)} second(s).")



if __name__ == "__main__":
    main()  

# def main():
#     # Step 1: Go to login page
#     driver.get("https://cdasiaonline.com/")

#     # Fill credentials
#     input_element = driver.find_element(By.ID, "user-id")
#     input_element.clear()
#     input_element.send_keys("accounting@onecfoph.co")
#     input_element = driver.find_element(By.ID, "user-password")
#     input_element.clear()
#     input_element.send_keys("HU9W19pr" + Keys.ENTER)

#     # Step 1.5: Handle Sign-in Alert
#     try:
#         wait.until(
#             EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
#         ).click()
#         print("Handled sign-in alert.")
#     except:
#         print("No sign-in alert shown.")

#     # Step 2: After login, click the "Libraries" dropdown
#     time.sleep(5)
#     wait.until(EC.element_to_be_clickable((By.ID, "library-menu-button"))).click()

#     # Step 3: Click the "Taxation" checkbox
#     wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Taxation')]/ancestor::label"))).click()
#     time.sleep(2) 

#     # Step 3.5: Click a neutral part of the page to close the dropdown
#     body_element = driver.find_element(By.TAG_NAME, "body")
#     body_element.click()
#     time.sleep(1) 

#     #Step 4 Click BIR
#     wait.until(EC.visibility_of_element_located((By.XPATH, "//li[.//span[contains(text(), 'Bureau of Internal Revenue (BIR)')]]"))).click()
#     time.sleep(2)

#     #Step 5 Click Rulings
#     element = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[.//span[contains(text(), 'Rulings (Numbered)')]]")))
#     driver.execute_script("arguments[0].scrollIntoView(true);", element)
#     time.sleep(0.5)
#     element.click()
#     time.sleep(2)

#     #5.5 Click the Page Number X amount of times
#     #The page - 1
#     for i in range (100):
#         time.sleep(1)
#         wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
#         print("Click next page button")
#         time.sleep(2)


#     #Step 6 Click on the first Regulation
#     time.sleep(3)
#     wait.until(EC.element_to_be_clickable((By.XPATH, "//table//tbody//tr[1]"))).click()

#     #Step 7 Switch to the new tab
#     time.sleep(2)
#     driver.switch_to.window(driver.window_handles[-1])

#     # print(extract_url())

#     case_data = {"libraryItemNo": 3,
#                 "libraryName": "Taxation",
#                 "contents": [
#                     {
#                         "contentItemNo": "1",
#                         "contentTitle": "Bureau of Internal Revenue (BIR)",
#                         "subContent": [
#                             {
#                                 "subcontentItemNo": "20",
#                                 "subcontentTitle": "Rulings (Numbered)",
#                                 "case": [
                                
#                                 ]
#                             }
#                         ]
#                     }
#                 ]
#             }

#     case_list = case_data["contents"][0]["subContent"][0]["case"]

#     #Edit count 
#     count = 2000

#     # for i in range(1600):
#     #     time.sleep(2)
#     #     wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
#     #     print("Click next page button")
#     #     count+=1
#     #     time.sleep(2)

#     time.sleep(2)

#     #Change this range to the number of pages
#     for i in range(700):  

#         count+=1

#         regulation_entry = {
#             "Ruling": f"{count}"
#         }

#         print(f"Scraping Regulation No: {count}")
        
#         # tabs = ["Original Law","Cited-In"]
#         # case_data[f"Regulation {i+1}"] = {}
        
#         #Handling of main tabs
#         tabs = ["Original Law"]

#         for tab in tabs:
#             content = scrape_tabs(tab)
#             if content:    
#                 # case_data[f"Regulation {i+1}"][tab] = content
#                 regulation_entry[tab] = content

#         #Handling of Cited References
#         regulation_entry["Original Law"]["Cited Reference"] = {}
#         # references = ["Laws", "Taxation", "Jurisprudence"]
#         references = get_references()

#         for reference in references: 
#             reference_content = scrape_cited_reference(reference)
#             if reference_content:
#                 regulation_entry["Original Law"]["Cited Reference"][reference] = reference_content


#         case_list.append(regulation_entry)

#         if i !=1:
#             time.sleep(2)
#             wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
#             print("Click next page button")
#             time.sleep(2)


#     print(json.dumps(case_data, indent=4, ensure_ascii=False))

#     filename = "BIR_Revenue_Rulings(Numbered)(4).json"

#     with open(filename, 'w') as file:
#         json.dump(case_data, file, indent=4)

#     time.sleep(10)

#     driver.quit()

# if __name__ == "__main__":
#     main()