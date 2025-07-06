from main import *

#Gets the URL
def extract_url():
    url = driver.current_url

    return url     

#Checks if the contents contains an Annex
def check_annex(content):

    result = False
    details_text = content["Original Law"]["Details"]
    annex_index = details_text.find("ANNEX A")

    if annex_index != -1:
        result = True

    return result

# Deletes the Annex
def delete_annex(content):
    
    details_text = content["Original Law"]["Details"]
    annex_index = details_text.find("ANNEX A")

    if annex_index != -1:
        content["Original Law"]["Details"] = details_text[:annex_index].strip()  #So this only gets all the paragraph before the index of ANNEX A
    
    return content    

# Gets the Annex
def return_annex():

    time.sleep(5)
    # Click the tab
    tab_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//button[normalize-space()='Original Law']")))
    driver.execute_script("arguments[0].click();", tab_button)

    # Wait for content panel to be visible and not hidden
    tab_panel = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//div[starts-with(@id, 'simple-tabpanel-') and not(@hidden)]"))
    )

    # Longer sleep to allow full content load (especially for slow internet)
    time.sleep(5)

    print("Scraping Annex Law...")

    all_p_tags = tab_panel.find_elements(By.XPATH, ".//p")
    
    #Count how many Annex are in the page:
    annex_count = 0

    for p in all_p_tags:
        text = p.text  # Get the text inside the <span>

        if "ANNEX" in text:  # Check if it contains 'ANNEX'
            annex_count += 1  # If yes, increment the count by 1


    #Loop wherein it will check if the text starts with ANNEX then it will store the line in the current_annex so it will be the header of each point
    annex_sections = {}
    curr_annex = None

    for p in all_p_tags:
        text = p.text.strip()
        links = p.find_elements(By.TAG_NAME, "a") 

        if text.startswith("ANNEX"):
            curr_annex = text
            annex_sections[curr_annex] = {"details": [], "links": []}
        elif curr_annex:
            annex_sections[curr_annex]["details"].append(text)
            for link in links:
                href = link.get_attribute("href")
                annex_sections[curr_annex]["links"].append(href)
    

    #Filtering, removing white spaces and empty
    for annex, lines in annex_sections.items():
        filtered_lines = []
        for line in lines["details"]:
            if line.strip():  
                filtered_lines.append(line)
        annex_sections[annex]["details"] = "\n\n".join(filtered_lines)


    #Get the Reference if it has a link
    if not annex_sections:
        return 
    
    return 

# Gets the Cited Reference Area
def scrape_cited_reference(reference_name):
      time.sleep(5)
      print(f"Scraping {reference_name}...")

      try:
            driver.find_element(By.XPATH, f"//button[.//h2[text()='{reference_name}']]")

            #Find the dropdown button of each reference
            dropdown = driver.find_element(By.XPATH, f"//button[.//h2[text()='{reference_name}']]")

            #Check if the button is alreay drop downed
            is_expanded = dropdown.get_attribute("aria-expanded") == "true"

            #If yes scrape
            reference_data = []

            if is_expanded:

                  # Scroll inside the scrollable container
                  container = driver.find_element(By.XPATH, "//div[@role='tabpanel' and @id='simple-tabpanel-0']")

                  last_height = 0
                  scroll_attempts = 0
                  max_scrolls = 10 

                  while scroll_attempts < max_scrolls:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
                        time.sleep(1)

                        print("scrolling...")

                        new_height = driver.execute_script("return arguments[0].scrollTop", container)

                        if new_height == last_height:
                              break 
                        last_height = new_height
                        scroll_attempts += 1

                  rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root table-row-even mui-2u4x71']/tr")

                  for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 3:
                              reference_entry = {
                                    "Reference Title": cols[0].text,
                                    "Title": cols[1].text,
                                    "Date": cols[2].text
                              }
                        reference_data.append(reference_entry) 

                  return reference_data
            
            # If not expanded, expand first, then scrape
            else: 
                  wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[.//h2[text()='{reference_name}']]"))).click()
                  time.sleep(3) 

                  # Scroll inside the scrollable container
                  container = driver.find_element(By.XPATH, "//div[@role='tabpanel' and @id='simple-tabpanel-0']")

                  last_height = 0
                  scroll_attempts = 0
                  max_scrolls = 10 

                  while scroll_attempts < max_scrolls:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
                        time.sleep(1)

                        print("scrolling...")

                        new_height = driver.execute_script("return arguments[0].scrollTop", container)

                        if new_height == last_height:
                              break 
                        last_height = new_height
                        scroll_attempts += 1

                  rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root table-row-even mui-2u4x71']/tr")

                  for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 3:
                              reference_entry = {
                                    "Reference Title": cols[0].text,
                                    "Title": cols[1].text,
                                    "Date": cols[2].text
                              }
                        reference_data.append(reference_entry) 

                  return reference_data
         
      except NoSuchElementException:
            print(f"No {reference_name} Referred")
            return 

# Gets the main content of the tab
def scrape_tabs(tab_name, retries=3):
    for attempt in range(retries):
        try:
            time.sleep(5)
            # Click the tab
            tab_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[normalize-space()='{tab_name}']")))
            driver.execute_script("arguments[0].click();", tab_button)

            # Wait for content panel to be visible and not hidden
            tab_panel = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[starts-with(@id, 'simple-tabpanel-') and not(@hidden)]"))
            )

            # Longer sleep to allow full content load (especially for slow internet)
            time.sleep(5)

            if tab_name == 'Original Law':

                print("Scraping Original Law...")

                url =extract_url()

                all_p_tags = tab_panel.find_elements(By.XPATH, ".//p")
                details = []
                footnotes = []
                in_footnotes = False
                # footnote = []

                for p in all_p_tags:
                    # Check if this is the footnote marker
                    p_class = p.get_attribute("class")

                    if p_class == "footnote-area":
                        in_footnotes = True
                        continue  # Skip the marker itself 

                    if in_footnotes:
                        # footnote.append(p.text.strip())
                        footnotes.append(p.text.strip())
                        
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

                date = details[0]
                ref = details [1]

                if footnotes:
                    return {
                        "Date": date,
                        "Reference Number": ref,
                        "url": url,
                        "Details": "\n\n".join(details[2:]),
                        "Footnote": "\n\n".join(footnotes) if footnotes else "No footnotes found"
                    }
                else:
                    return {
                        "Date": date,
                        "Reference Number": ref,
                        "url": url,
                        "Details": "\n\n".join(details[2:]),
                    } 

            else:
                # Re-fetch paragraphs inside the visible tab panel
                paragraphs = tab_panel.find_elements(By.XPATH, ".//p | .//span[@class]")
                content = "\n\n".join(p.text.strip() for p in paragraphs if p.text.strip())

                # Fallback: if no paragraphs, try divs
                if not content.strip():
                    divs = tab_panel.find_elements(By.XPATH, ".//div")
                    content = "\n\n".join(div.text.strip() for div in divs if div.text.strip())

                print(f"Finished scraping '{tab_name}' tab.")
                return content if content.strip() else None

        except StaleElementReferenceException as e:
            print(f"Attempt {attempt+1} - Stale element: {e}. Retrying...")
            time.sleep(3)
        except Exception as e:
            print(f"Attempt {attempt+1} - Error scraping '{tab_name}': {e}")
            time.sleep(3)

    print(f"Giving up on '{tab_name}' tab after {retries} attempts.")
    return None

# Gets the cited refernce header
def get_references():
    output = []
    h2_elements = driver.find_elements(By.XPATH, "//h2[contains(@class, 'MuiTypography-h2')]")

    for elem in h2_elements:
        output.append(elem.text)

    return output

def scrape(url, count):

    driver.get(url)

    regulation_entry = {
        "Ruling": f"{count}"
    }

    # Handling of main tabs
    tab = "Original Law"

    content = scrape_tabs(tab)

    if content:    
        regulation_entry[tab] = content

    #Handling of Cited References
    regulation_entry["Original Law"]["Cited Reference"] = {}

    # references = ["Laws", "Taxation", "Jurisprudence"]
    references = get_references()

    for reference in references: 
        reference_content = scrape_cited_reference(reference)
        if reference_content:
            regulation_entry["Original Law"]["Cited Reference"][reference] = reference_content

    return regulation_entry