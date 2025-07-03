from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

import time
import json

from function import *


driver = webdriver.Chrome()
wait = WebDriverWait(driver, 30)

def main():
    # Step 1: Go to login page
    driver.get("https://cdasiaonline.com/")

    # Fill credentials
    input_element = driver.find_element(By.ID, "user-id")
    input_element.clear()
    input_element.send_keys("accounting@onecfoph.co")
    input_element = driver.find_element(By.ID, "user-password")
    input_element.clear()
    input_element.send_keys("HU9W19pr" + Keys.ENTER)

    # Step 1.5: Handle Sign-in Alert
    try:
        wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
        ).click()
        print("Handled sign-in alert.")
    except:
        print("No sign-in alert shown.")

    # Step 2: After login, click the "Libraries" dropdown
    time.sleep(5)
    wait.until(EC.element_to_be_clickable((By.ID, "library-menu-button"))).click()

    # Step 3: Click the "Taxation" checkbox
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Taxation')]/ancestor::label"))).click()
    time.sleep(2) 

    # Step 3.5: Click a neutral part of the page to close the dropdown
    body_element = driver.find_element(By.TAG_NAME, "body")
    body_element.click()
    time.sleep(1) 

    #Step 4 Click BIR
    wait.until(EC.visibility_of_element_located((By.XPATH, "//li[.//span[contains(text(), 'Bureau of Internal Revenue (BIR)')]]"))).click()
    time.sleep(2)

    #Step 5 Click Rulings
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[.//span[contains(text(), 'Rulings (Numbered)')]]")))
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(0.5)
    element.click()
    time.sleep(2)

    #5.5 Click the Page Number X amount of times
    #The page - 1
    for i in range (100):
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
        print("Click next page button")
        time.sleep(2)


    #Step 6 Click on the first Regulation
    time.sleep(3)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//table//tbody//tr[1]"))).click()

    #Step 7 Switch to the new tab
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])

    # print(extract_url())

    case_data = {"libraryItemNo": 3,
                "libraryName": "Taxation",
                "contents": [
                    {
                        "contentItemNo": "1",
                        "contentTitle": "Bureau of Internal Revenue (BIR)",
                        "subContent": [
                            {
                                "subcontentItemNo": "20",
                                "subcontentTitle": "Rulings (Numbered)",
                                "case": [
                                
                                ]
                            }
                        ]
                    }
                ]
            }

    case_list = case_data["contents"][0]["subContent"][0]["case"]

    #Edit count 
    count = 2000

    # for i in range(1600):
    #     time.sleep(2)
    #     wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
    #     print("Click next page button")
    #     count+=1
    #     time.sleep(2)

    time.sleep(2)

    #Change this range to the number of pages
    for i in range(700):  

        count+=1

        regulation_entry = {
            "Ruling": f"{count}"
        }

        print(f"Scraping Regulation No: {count}")
        
        # tabs = ["Original Law","Cited-In"]
        # case_data[f"Regulation {i+1}"] = {}
        
        #Handling of main tabs
        tabs = ["Original Law"]

        for tab in tabs:
            content = scrape_tabs(tab)
            if content:    
                # case_data[f"Regulation {i+1}"][tab] = content
                regulation_entry[tab] = content

        #Handling of Cited References
        regulation_entry["Original Law"]["Cited Reference"] = {}
        # references = ["Laws", "Taxation", "Jurisprudence"]
        references = get_references()

        for reference in references: 
            reference_content = scrape_cited_reference(reference)
            if reference_content:
                regulation_entry["Original Law"]["Cited Reference"][reference] = reference_content


        case_list.append(regulation_entry)

        if i !=1:
            time.sleep(2)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))).click()
            print("Click next page button")
            time.sleep(2)


    print(json.dumps(case_data, indent=4, ensure_ascii=False))

    filename = "BIR_Revenue_Rulings(Numbered)(4).json"

    with open(filename, 'w') as file:
        json.dump(case_data, file, indent=4)

    time.sleep(10)

    driver.quit()

if __name__ == "__main__":
    main()