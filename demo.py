import subprocess
from time import sleep
from playwright.sync_api import sync_playwright
import subprocess
import time
from bs4 import BeautifulSoup, Comment



CHROME_EXECUTABLE_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA_DIR = "/Users/{your user name here}/Library/Application Support/Google/Chrome/"
CHROME_PROFILE_DIRECTORY = "Default"
REMOTE_DEBUGGING_PORT = 9222
REMOTE_HOST = 'localhost'
TARGET_URL = "https://chat.openai.com/"

def launch_browser():
    args = [
        "--no-first-run",
        "--flag-switches-begin",
        "--flag-switches-end",
        f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
        f"--profile-directory={CHROME_PROFILE_DIRECTORY}"
    ]
    subprocess.Popen([CHROME_EXECUTABLE_PATH] + args)
    wait_for_port(REMOTE_HOST, REMOTE_DEBUGGING_PORT)


import socket
import time

def is_port_listening(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)  # Setting a brief timeout
            result = sock.connect_ex((host, port))
            return result == 0  # True if the port is open
    except ConnectionRefusedError as error:
        print(error)
        return False  # Port is not open yet

def wait_for_port(host, port, timeout=20, retry_interval=1):
    start_time = time.time()
    while not is_port_listening(host, port):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for port {port} to listen")
        time.sleep(retry_interval)

def clean_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script, style, head, meta, and link elements
    for element in soup(["script", "style", "head", "meta", "link"]):
        element.decompose()

    # Optionally, remove comments
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Define the attributes we want to keep for certain tags
    attributes_to_keep = {
        'a': ['href', 'title'],
        'img': ['src', 'alt'],
        'input': ['type', 'placeholder', 'name', 'value'],
        'button': ['type', 'name'],
        'form': ['action', 'method'],
        'textarea': ['placeholder', 'name']
    }

    # Loop through all tags and remove attributes not listed to keep
    for tag in soup.find_all(True):
        if tag.name in attributes_to_keep:
            # Keep only the specified attributes for this tag
            for attr in list(tag.attrs):
                if attr not in attributes_to_keep[tag.name]:
                    del tag.attrs[attr]
        else:
            # If the tag is not in the list, remove all attributes
            tag.attrs = {}

    # Get the cleaned HTML as a string
    cleaned_html = str(soup)
    return cleaned_html

def connect_to_browser():
    with sync_playwright() as p:
        endpoint_url = f"http://localhost:{REMOTE_DEBUGGING_PORT}"
        browser = p.chromium.connect_over_cdp(endpoint_url)
        default_context = browser.contexts[0]
        page = default_context.pages[0]
        page.goto(TARGET_URL)
        page.wait_for_load_state('networkidle')


        # Retrieve the raw HTML content
        html_content = page.content()

        # Clean the HTML content using the function defined above
        cleaned_html_content = clean_html_content(html_content)
        print("Cleaned HTML Content of the page:", cleaned_html_content)  # Optional: you can remove this print later

        return browser, cleaned_html_content  # Return the browser context and the cleaned HTML content
def main():
    launch_browser()
    context = connect_to_browser()
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        print("Script interrupted. Closing browser context.")
    finally:
        context.close()

if __name__ == "__main__":
    main()

