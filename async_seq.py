import re
import time
import asyncio
from playwright.async_api import Playwright, async_playwright, expect, Page, TimeoutError
import json
from pathlib import Path

BASE_URL = "https://cdasiaonline.com/"
USERNAME = "accounting_tax@onecfoph.co"
PASSWORD = "GXh14s2H1Q"

OUTPUT_PATH = Path("scraped_output.json")

content_group_name = "Implementing Rules and Regulations"
content_subgroup_name = "Republic Acts"


# Constants for manual testing
MANUAL_MODE = False         # Toggle this on/off for testing
MANUAL_START_PAGE = 1      # Page number to start from (1-based)
MANUAL_START_ROW = 3     # Row number to start from (1-based)


CONFIG = {
    "libraryItemNo": 3,
    "libraryName": "Taxation",
    "contents": [
        {
            "contentItemNo": 11,
            "contentTitle": content_group_name,
            "subContent": [{
                "subContentItemNo": 3,
                "subContentTitle": content_subgroup_name,
                "case": []
            }]
        }
    ]
}

async def fill_login(page: Page):
    await page.wait_for_selector("#user-id")
    await page.fill("#user-id", USERNAME)
    await page.fill("#user-password", PASSWORD)
    await page.keyboard.press("Enter")

    try:
        await page.wait_for_selector("button:has-text('Continue')", timeout=5000)
        await page.click("button:has-text('Continue')")
        print("[✅STATUS] Handled sign-in alert.")
    except:
        print("[ℹ️STATUS] No sign-in alert shown.")

async def run(playwright: Playwright) -> None:
    start_time = time.time()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://cdasiaonline.com/signin?callbackUrl=https%3A%2F%2Fcdasiaonline.com%2F")
    try:
        await fill_login(page)
        await page.get_by_role("button", name="Libraries").click()
        await page.get_by_role("checkbox", name="controlled").check()
        await page.locator(".MuiBackdrop-root").click()

        await page.get_by_role("button", name=content_group_name).click()
        await page.get_by_role("button", name=content_subgroup_name).click()

        await scrape_table(page)

        await asyncio.sleep(2)
    except Exception as e:
        print(e)
    finally:
        await context.close()
        await browser.close()
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n✅ Finished scraping document(s) in {elapsed:.2f} seconds.")

async def display_document_info(date: str, ref_number: str, subject_info: str, to_info: str, url: str,
                               cited_reference: dict, details: dict, elapsed_time: float) -> None:
    print("\n [ℹ️STATUS] Displaying Document Information:")
    print("\t ================INFO================ \n ")
    print(f"\t[⏱️ Scrape Time]: {elapsed_time:.2f} seconds")
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
    print(f"\t[ℹ️ Details]: {details if details else None}...")
    print(f"\t[ℹ️ Cited Reference]: {cited_reference if cited_reference else None}...")
    print("\t ================INFO================ \n ")

    case_item = {
        "Date": date,
        "Reference Number": ref_number,
        "Subject": subject_info,
        "To": to_info,
        "URL": url,
        "Details": details,
        "Cited References": cited_reference
    }


    await save_case_item_to_json(case_item)

async def get_details(page: Page) -> dict:
    retries = 3
    for attempt in range(retries):
        try:
            tab_panel = page.locator("//div[starts-with(@id, 'simple-tabpanel-') and not(@hidden)]").first
            await tab_panel.wait_for(timeout=10_000)

            print(f"[✅ STATUS] Content Panel Loaded on Attempt {attempt + 1}")

            all_p_tags = await tab_panel.locator("p").all()
            print(f"[DEBUG] Found {len(all_p_tags)} <p> tags")

            details, footnotes, annex_sections = [], [], {}
            curr_annex = None

            for p in all_p_tags:
                p_class = await p.get_attribute("class")
                text = (await p.inner_text()).strip()
                links = await p.locator("a").all()

                if not text:
                    continue
                if p_class == "footnote-area":
                    footnotes.append(text)
                elif text.startswith("ANNEX"):
                    curr_annex = text
                    annex_sections[curr_annex] = {"details": [], "links": []}
                elif curr_annex:
                    annex_sections[curr_annex]["details"].append(text)
                    for link in links:
                        href = await link.get_attribute("href")
                        annex_sections[curr_annex]["links"].append(href)
                else:
                    details.append(text)

            details = [line for line in details if line.strip()]
            footnotes = [line for line in footnotes if line.strip()]
            for annex, lines in annex_sections.items():
                lines["details"] = "\n\n".join([line.strip() for line in lines["details"] if line.strip()])

            result = {
                "Details": "\n\n".join(details[2:]),
                "Footnote": "\n\n".join(footnotes) if footnotes else "None",
                "Annexes": annex_sections if annex_sections else "None"
            }

            print(f"[DEBUG] Returning details: {result}")
            return result

        except Exception as e:
            print(f"[❌ ERROR] Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2)

    print(f"[❌ ERROR] Giving up after {retries} failed attempts.")
    return None

async def get_cited_reference(page: Page) -> dict:
    cited = {}
    headers = page.locator("h2.MuiTypography-root")
    for i in range(await headers.count()):
        header = headers.nth(i)
        text = (await header.inner_text()).strip()
        try:
            accordion = header.locator("xpath=ancestor::div[contains(@class, 'MuiAccordion-root')]")
            summary = accordion.locator("button.MuiAccordionSummary-root")
            details = accordion.locator("div.MuiAccordionDetails-root")
            await summary.click()
            await asyncio.sleep(0.1)
            if not await details.is_visible():
                await summary.click()
            rows = details.locator("tbody tr")
            records = []
            for j in range(await rows.count()):
                cells = rows.nth(j).locator("td")
                if await cells.count() >= 3:
                    rec = {
                        "Reference Number": (await cells.nth(0).inner_text()).strip(),
                        "Title": (await cells.nth(1).inner_text()).strip(),
                        "Date": (await cells.nth(2).inner_text()).strip()
                    }
                    records.append(rec)
            if records:
                cited[text] = records
        except Exception as e:
            (f"[⚠️ Cited Ref Error] {text}: {e}")
    return cited


async def get_cited_reference_header(page: Page) -> list[str]:
    try:
        await page.wait_for_load_state("load")

        h3_elements = await page.locator('h2').all_text_contents()
        print(f'REFERENCE HEADER {h3_elements}')
        await asyncio.sleep(1)  # short wait

        return h3_elements

    except Exception as e:
        print(f"[❌ ERROR in get_cited_reference_header()] {e}")
        return []



async def get_url(page: Page) -> str:
    return page.url

async def get_ref_number(page: Page) -> str:
    try:
        element = await page.wait_for_selector("#reference_no > span", timeout=1000)
        reg_no = (await element.inner_text()).strip()
        print(f"[✅STATUS] Found Regulation Number: {reg_no}")
        return reg_no
    except Exception as e:
        print(f"[⚠️FALLBACK TRIGGERED] Trying Fallback:")
        try:
            element = await page.wait_for_selector("#document-container > p:nth-child(3)", timeout=10_000)
            reg_no = (await element.inner_text()).strip()
            print(f"[✅STATUS] Found Regulation Number (Fallback): {reg_no}")
            return reg_no
        except Exception as e:
            print(f"[❌STATUS] Error getting Regulation Number: {e}")
            return None

async def get_subject(page: Page) -> str:
    try:
        trow = await page.wait_for_selector("#document-container > div:nth-child(4) > table > tbody > tr:nth-child(1)", timeout=1000)
        td_elements = await trow.query_selector_all("td")

        if len(td_elements) <= 2:
            print("[⚠️STATUS] Index is less than or equal to 2.")
            print("[⚠️STATUS] Subject is not available for the document.")
            return "None" 

        subject_parts = [(await td.inner_text()).strip() for td in td_elements[2:]]
        subject = " ".join(subject_parts)

        print(f"[✅STATUS] Found Subject: {subject}")
        return subject
    except Exception as e:
        print(f"[❌STATUS] Error getting Subject: {e}")
        return "None"

async def get_doc_date(page: Page) -> str:
    try:
        element = await page.wait_for_selector("#document-container > p:nth-child(2)", timeout=10_000)
        doc_date = (await element.inner_text()).strip()
        print(f"[✅STATUS] Found Document Date: {doc_date}")
        return doc_date
    except Exception as e:
        print(f"[❌STATUS] Error getting Document Date: {e}")
        return "None"

async def get_to_info(page: Page) -> str:
    try:
        trow = await page.wait_for_selector("#document-container > div:nth-child(4) > table > tbody > tr:nth-child(3)", timeout=1000)
        td_elements = await trow.query_selector_all("td")
        to_info_parts = [(await td.inner_text()).strip() for td in td_elements[2:]]
        to_info = " ".join(to_info_parts)
        print(f"[✅STATUS] Found TO Info: {to_info}")
        return to_info
    except Exception as e:
        print(f"[❌STATUS] The TO Info is not available for the document")
        return "None"

async def save_case_item_to_json(case_item: dict):
    try:
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = CONFIG

        existing_refs = {
            entry["Reference Number"]
            for entry in data["contents"][0]["subContent"][0]["case"]
        }

        if case_item["Reference Number"] in existing_refs:
            print(f"[⚠️STATUS] Duplicate found. Skipping save for: {case_item['Reference Number']}")
            return

        data["contents"][0]["subContent"][0]["case"].append(case_item)

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"[💾STATUS] Appended item to {OUTPUT_PATH}")

    except Exception as e:
        print(f"[❌ERROR] Failed to save case item: {e}")




async def extract_document_data(page: Page, elapsed_time: float) -> dict:
    date = await get_doc_date(page)
    reference_number = await get_ref_number(page)
    subject = await get_subject(page)
    to_info = await get_to_info(page)
    url = await get_url(page)
    details = await get_details(page)
    cited_reference = await get_cited_reference(page)

    return {
        "Date": date,
        "Reference Number": reference_number,
        "Subject": subject,
        "To": to_info,
        "URL": url,
        "Scrape Time (s)": round(elapsed_time, 2),
        "Details": details,
        "Cited References": cited_reference
    }

async def load_table(page: Page, selector: str, retries: int = 3, delay: float = 2.0) -> bool:
    for attempt in range(1, retries + 1):
        try:
            await page.wait_for_selector(selector, timeout=5000)
            print(f"[✅STATUS] Table loaded on attempt {attempt}")
            return True
        except TimeoutError:
            print(f"[⚠️WARNING] Attempt {attempt} failed. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    print("[❌STATUS] Table not found after retries.")
    return False

async def go_to_next_page(page: Page) -> bool:
    try:
        await page.get_by_role("button", name="Go to next page").click()
        # Wait for one of the table rows to load (not just domcontentloaded)
        await page.wait_for_selector("table tbody tr", timeout=5000)
        return True
    except Exception as e:
        print(f"[⚠️] Could not go to next page: {e}")
        return False

async def process_table_rows(page: Page, context, selector: str, row_count, scraped_so_far: int, start_row: int = 0) -> int:
    rows = page.locator(f"{selector} tbody tr")
    row_count = await rows.count()
    new_scraped = 0
    total_start = time.time()

    for i in range(start_row, row_count):
        print(f"[➡️] Clicking row {i + 1}/{row_count}")
        success = False
        new_tab = None

        for attempt in range(2):
            try:
                rows = page.locator(f"{selector} tbody tr")
                async with context.expect_page(timeout=7000) as new_page_info:
                    await rows.nth(i).click()
                new_tab = await new_page_info.value
                await new_tab.wait_for_load_state("domcontentloaded")

                print(f"[🆕] Opened new tab for row {i + 1} (attempt {attempt + 1})")

                row_start = time.time()
                data = await extract_document_data(new_tab, elapsed_time=0)
                elapsed_time = time.time() - row_start
                data["Scrape Time (s)"] = round(elapsed_time, 2)

                await display_document_info(
                    data["Date"],
                    data["Reference Number"],
                    data["Subject"],
                    data["To"],
                    data["URL"],
                    data["Cited References"],
                    data["Details"],
                    data["Scrape Time (s)"]
                )

                success = True
                new_scraped += 1

            except Exception as e:
                print(f"[⚠️] Attempt {attempt + 1} failed for row {i + 1}: {e}")
                await asyncio.sleep(0.5)

            finally:
                if new_tab:
                    try:
                        await new_tab.close()
                        print(f"[❌] Closed tab for row {i + 1}")
                    except Exception as close_err:
                        print(f"[⚠️] Failed to close tab for row {i + 1}: {close_err}")

            if success:
                break

        if not success:
            print(f"[❌] Skipped row {i + 1} after 2 attempts.")

    total_elapsed = time.time() - total_start
    print(f"[✅] Finished scraping {new_scraped} documents in {total_elapsed:.2f} seconds.")
    return new_scraped

async def get_rows_on_current_page(page: Page, selector: str) -> int:
    await page.wait_for_selector(f"{selector} tbody tr")  # Wait for at least one row
    rows = page.locator(f"{selector} tbody tr")
    count = await rows.count()
    print(f"[📄STATUS] Found {count} rows on page.")
    return count

async def scrape_table(page: Page):
    global MANUAL_MODE
    table_selector = "body > div > main > div > div > div > div > div > div > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation1.MuiTableContainer-root.mui-rdu9rc > table"

    total_documents = await get_total_documents(page)
    print(f"[TOTAL DOCUMENTS] {total_documents}")

    if not await load_table(page, table_selector):
        return

    context = page.context
    scraped_documents = 0
    page_counter = 1

    # MANUAL MODE JUMP LOGIC
    if MANUAL_MODE:
        print(f"[🛠️ MANUAL MODE ENABLED] Jumping to page {MANUAL_START_PAGE}...")
        while page_counter < MANUAL_START_PAGE:
            if not await go_to_next_page(page):
                print(f"[❌ ERROR] Failed to reach manual start page {MANUAL_START_PAGE}")
                return
            page_counter += 1
        print(f"[✅] Now at manual start page: {page_counter}")

    while scraped_documents < total_documents:
        print(f"[📄] Scraping Page: {page_counter}")
        rows_on_page = await get_rows_on_current_page(page, table_selector)

        # Determine the start row
        start_row = (MANUAL_START_ROW -1 ) if MANUAL_MODE and page_counter == MANUAL_START_PAGE else 0
        print(f"[ℹ️] Starting from row {start_row + 1}")

        # Slice the rows manually
        rows = page.locator(f"{table_selector} tbody tr")
        row_count = await rows.count()
        if start_row >= row_count:
            print(f"[⚠️ WARNING] Start row {start_row} exceeds row count {row_count}. Skipping page.")
        else:
            scraped_in_this_page = await process_table_rows(page, context, table_selector, row_count=rows_on_page, scraped_so_far=scraped_documents, start_row=start_row)
            scraped_documents += scraped_in_this_page

        if scraped_documents >= total_documents:
            break

        if not await go_to_next_page(page):
            break

        page_counter += 1
        # Reset start row after first manual page
        if MANUAL_MODE:
            MANUAL_MODE = False


async def get_total_documents(page: Page) -> int:
    selector = "body > div > main > div > div > div > div > div > div > div.MuiStack-root.mui-8rqxm6 > div.MuiStack-root.mui-1r3zmyn > span"

    try:
        await page.wait_for_selector(selector, timeout=5000)

        for _ in range(10):
            text = (await page.locator(selector).inner_text()).strip()
            if "Searching" not in text and text[0].isdigit():
                number_part = text.split()[0].replace(",", "")
                return int(number_part)
            await asyncio.sleep(0.5)

        print("[❌STATUS] Still stuck on 'Searching' after wait.")
        return 0

    except Exception as e:
        print("[❌STATUS] Could not determine document count.")
        print(f"[Error] {e}")
        return 0

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    asyncio.run(main())