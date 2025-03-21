from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import pickle
import os
import re

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--headless")  # Uncomment for production
    options.add_argument("--user-agent=Mozilla/5.0")
    driver = webdriver.Chrome(options=options)
    return driver

def save_cookies(driver, path="Facebook_Cookies.pkl"):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("✅ Cookies saved to", path)

def load_cookies(driver, path="Facebook_Cookies.pkl"):
    if os.path.exists(path):
        with open(path, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("✅ Cookies loaded from", path)
    else:
        print("❌ No cookies file found. Please login first.")

def login_facebook(driver):
    driver.get("https://www.facebook.com")
    time.sleep(2)
    if not os.path.exists("Facebook_Cookies.pkl"):
        driver.find_element(By.ID, "email").send_keys("your_email")
        driver.find_element(By.ID, "pass").send_keys("your_password")
        driver.find_element(By.NAME, "login").click()
        time.sleep(5)
        save_cookies(driver)
    else:
        load_cookies(driver)
        driver.get("https://www.facebook.com/")
        time.sleep(2)

def parse_post_text(raw_text):
    """Parse raw post text into structured metadata."""
    metadata = {
        "content": "",
        "username": "",
        "timestamp": "",
        "reactions": {"likes": 0, "comments": 0, "shares": 0},
        "hashtags": []
    }
    
    lines = raw_text.split("\n")
    if lines:
        metadata["username"] = lines[0].strip()  # e.g., "Best of Kumar Vishwas"
    if len(lines) > 1:
        metadata["timestamp"] = lines[1].strip()  # e.g., "19 March at 10:25"
    
    # Extract content (before reactions)
    content_lines = []
    reaction_start = False
    for line in lines:
        if "All reactions:" in line:
            reaction_start = True
            break
        if line.strip() and line != "·" and not re.match(r"^\d+$", line):
            content_lines.append(line.strip())
    metadata["content"] = " ".join(content_lines[len(lines[0:2]):]).strip()  # Skip username and timestamp

    # Extract reactions
    if reaction_start:
        reaction_index = lines.index("All reactions:") + 1
        if len(lines) > reaction_index:
            metadata["reactions"]["likes"] = int(lines[reaction_index].replace("K", "000").replace(".", "")) if "K" in lines[reaction_index] else int(lines[reaction_index] or 0)
        if len(lines) > reaction_index + 2:
            metadata["reactions"]["comments"] = int(lines[reaction_index + 2] or 0)
        if len(lines) > reaction_index + 3:
            metadata["reactions"]["shares"] = int(lines[reaction_index + 3] or 0)

    # Extract hashtags
    metadata["hashtags"] = re.findall(r"#\w+", raw_text)
    
    return metadata

def scrape_facebook_posts(page_url):
    driver = setup_driver()
    login_facebook(driver)

    driver.get(page_url)
    time.sleep(5)

    print("📜 Scrolling to load posts...")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    posts_data = []
    posts = driver.find_elements(By.CSS_SELECTOR, "div[aria-posinset]")
    print(f"🔍 Found {len(posts)} posts with aria-posinset")

    for post in posts:
        try:
            posinset = post.get_attribute("aria-posinset") or "unknown"
            print(f"\nProcessing post with aria-posinset={posinset}")
            raw_text = post.text.strip()
            print(f"Raw post text: '{raw_text}'")

            # Parse text into metadata
            metadata = parse_post_text(raw_text)

            # Image extraction
            image_urls = []
            try:
                images = post.find_elements(By.TAG_NAME, "img")  # Multiple images
                for image in images:
                    url = image.get_attribute("src")
                    if url and "emoji.php" not in url:  # Skip emoji images
                        image_urls.append(url)
                        print(f"📷 Found image: {url}")
            except:
                print("No images found")

            # Video extraction
            video_urls = []
            try:
                videos = post.find_elements(By.TAG_NAME, "video")
                for video in videos:
                    url = video.get_attribute("src")
                    if url:
                        video_urls.append(url)
                        print(f"📹 Found video: {url}")
            except:
                print("No videos found")

            # Save structured data
            if metadata["content"] or image_urls or video_urls:
                post_data = {
                    "post": {
                        "content": metadata["content"],
                        "hashtags": metadata["hashtags"]
                    },
                    "metadata": {
                        "username": metadata["username"],
                        "timestamp": metadata["timestamp"],
                        "reactions": metadata["reactions"],
                        "aria_posinset": posinset
                    },
                    "images": image_urls[0],
                    "videos": video_urls
                }
                posts_data.append(post_data)
                print(f"📌 Saved post (aria-posinset={posinset}): {metadata['content'][:100]}")

        except Exception as e:
            print(f"❌ Error extracting post (aria-posinset={posinset}): {e}\n{traceback.format_exc()}")

    with open("facebook_posts.json", "w", encoding="utf-8") as f:
        json.dump(posts_data, f, indent=4)

    print(f"✅ {len(posts_data)} posts saved successfully!")
    driver.quit()

if __name__ == "__main__":
    scrape_facebook_posts("https://www.facebook.com/profile.php?id=100095207616182")