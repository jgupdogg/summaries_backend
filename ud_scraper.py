
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import random
import os
import tempfile
from proxy_pool import *


# scraper object with proxy pool and anti bot detection
class UDScraper:
    def __init__(self, use_proxy=True):
        self.driver = None
        self.use_proxy = use_proxy
        self.proxy_pool = self.get_proxy_pool() if use_proxy else []
        print(f"Initialized UDScraper with use_proxy={use_proxy}")
        if use_proxy:
            print(f"Loaded {len(self.proxy_pool)} proxies")

    def get_proxy_pool(self):
        proxies = get_best_proxies()  # Assuming this function is defined elsewhere
        print(f"Fetched {len(proxies)} proxies")
        return proxies

    def get_random_proxy(self):
        if not self.proxy_pool:
            print("Proxy pool is empty. Refreshing...")
            self.proxy_pool = self.get_proxy_pool()
        if self.proxy_pool:
            proxy = random.choice(self.proxy_pool)
            print(f"Selected proxy: {proxy['ip']}:{proxy['port']}")
            return proxy
        else:
            print("No proxies available")
            return None

    def setup_proxy_extension(self, proxy):
        # Use a temporary directory instead of relying on __file__
        PROXY_FOLDER = os.path.join(tempfile.gettempdir(), 'ud_scraper_proxy_folder')
        os.makedirs(PROXY_FOLDER, exist_ok=True)

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "storage",
                "webRequest",
                "webRequestAuthProvider"
            ],
            "host_permissions": [
                "<all_urls>"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "minimum_chrome_version": "22.0.0"
        }
        """

        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy['ip']}",
                    port: parseInt({proxy['port']})
                }},
                bypassList: ["localhost"]
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy.get('username', '')}",
                    password: "{proxy.get('password', '')}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """

        with open(os.path.join(PROXY_FOLDER, "manifest.json"), "w") as f:
            f.write(manifest_json)
        with open(os.path.join(PROXY_FOLDER, "background.js"), "w") as f:
            f.write(background_js)

        return PROXY_FOLDER

    def setup_driver(self, proxy=None):
        print("Setting up driver...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-extensions")
        
        if proxy:
            print(f"Using proxy: {proxy['ip']}:{proxy['port']}")
            proxy_folder = self.setup_proxy_extension(proxy)
            options.add_argument(f"--load-extension={proxy_folder}")
        else:
            print("Not using a proxy")
        
        driver = uc.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        print("Driver setup complete")
        return driver
    
    def make_request(self, url, max_retries=3):
        print(f"Making request to {url}")
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1} of {max_retries}")
            proxy = self.get_random_proxy() if self.use_proxy else None
            self.driver = self.setup_driver(proxy)
            try:
                print(f"Navigating to {url}")
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("Page loaded successfully")
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                self.close_driver()
                return soup
            except (TimeoutException, WebDriverException) as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                print(f"Retrying{'with a new proxy' if self.use_proxy else ''}...")
                self.close_driver()
                time.sleep(2 ** attempt)  # Exponential backoff
        
        print(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass  # Ignore any exceptions during driver closure
        self.driver = None
