import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile


def initialize_driver() -> WebDriver:
    options = Options()
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("permissions.default.desktop-notification", 2)
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
    )

    # Path to uBlock extension .xpi file
    ublock_path = os.path.join(os.path.dirname(__file__), "ublock_origin-1.64.0.xpi")

    # Create profile and add extension
    profile = FirefoxProfile()
    profile.add_extension(extension=ublock_path)

    # 🔄 Attach profile via options instead of `firefox_profile=...`
    options.profile = profile

    driver = webdriver.Firefox(options=options)
    
    driver.maximize_window()
    
    return driver


    # # Optional: Verify uBlock is active manually
    # driver.get("about:addons")
    # input("👉 Check if uBlock Origin is active in the Add-ons Manager. Press Enter to continue...")

