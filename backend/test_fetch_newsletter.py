"""
Fetch and inspect AINews newsletter structure.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup

async def fetch_and_inspect():
    """Fetch newsletter and inspect HTML structure."""
    url = "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"

    print(f"Fetching newsletter from: {url}\n")

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title_elem = soup.find("title")
    print(f"Title: {title_elem.text if title_elem else 'Not found'}\n")

    # Find main content area
    print("Looking for content structure...\n")

    # Common newsletter structures
    article = soup.find("article") or soup.find("div", class_=lambda x: x and ("content" in x or "post" in x))

    if article:
        print("Found article/content div")

        # Find headers
        headers = article.find_all(["h1", "h2", "h3", "h4"])
        print(f"\nHeaders found: {len(headers)}")
        for i, h in enumerate(headers[:5]):  # Show first 5
            print(f"  {i+1}. <{h.name}> {h.get_text(strip=True)[:80]}...")

        # Find list items
        list_items = article.find_all("li")
        print(f"\nList items found: {len(list_items)}")
        for i, li in enumerate(list_items[:5]):  # Show first 5
            text = li.get_text(strip=True)[:100]
            links = [a.get("href") for a in li.find_all("a")]
            print(f"  {i+1}. {text}...")
            if links:
                print(f"      Links: {links[:2]}")

        # Find paragraphs
        paragraphs = article.find_all("p")
        print(f"\nParagraphs found: {len(paragraphs)}")
        for i, p in enumerate(paragraphs[:3]):  # Show first 3
            print(f"  {i+1}. {p.get_text(strip=True)[:100]}...")

    else:
        print("No article/content div found. Showing raw structure:")
        # Show all top-level divs
        for div in soup.find_all("div", recursive=False)[:5]:
            classes = div.get("class", [])
            print(f"  <div class='{' '.join(classes) if classes else 'none'}'> ...")

if __name__ == "__main__":
    asyncio.run(fetch_and_inspect())
