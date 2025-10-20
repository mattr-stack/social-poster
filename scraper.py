import requests
import extruct
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

    # --- Helper Functions ---

def first_non_empty(*args):
        """Returns the first non-empty (and not None) argument."""
        for arg in args:
            if arg and isinstance(arg, str) and arg.strip():
                return arg.strip()
        return ""

def plain(text):
        """Strips HTML tags, entities, and extra whitespace."""
        if not text:
            return ""
        text = BeautifulSoup(text, 'html.parser').get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

def clip(text, max_len):
        """Clips text to a max length, adding an ellipsis if needed."""
        if not text or len(text) <= max_len:
            return text
        last_space = text.rfind(' ', 0, max_len - 3)
        if last_space == -1:
            return text[:max_len - 3] + '...'
        return text[:last_space] + '...'

    # --- The Main Scraper Class ---

class MetadataScraper:
        """
        A robust metadata scraper that translates your proven JS logic to Python.
        It prioritizes Open Graph (OG) tags and provides comprehensive fallbacks.
        """
        def scrape(self, article_url: str):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(article_url, headers=headers, allow_redirects=True, timeout=10)
                response.raise_for_status()
                html = response.text
                if not html or len(html) < 500:
                    print(f"Warning: HTML for {article_url} is too short or empty.")
                    return None
                final_url = response.url
            except requests.RequestException as e:
                print(f"Error fetching {article_url}: {e}")
                return None

            soup = BeautifulSoup(html, 'html.parser')

            meta_tags = {
                tag.get('property', tag.get('name')).lower(): tag.get('content')
                for tag in soup.find_all('meta')
                if (tag.get('property') or tag.get('name')) and tag.get('content')
            }
            
            json_ld_data = extruct.extract(html, base_url=final_url, syntaxes=['json-ld'])
            ld = self._parse_json_ld(json_ld_data)

            og_title = meta_tags.get("og:title", "")
            og_desc = meta_tags.get("og:description", "")
            og_img = first_non_empty(
                meta_tags.get("og:image:secure_url"),
                meta_tags.get("og:image"),
                meta_tags.get("og:image:url")
            )

            title = first_non_empty(
                og_title,
                meta_tags.get("twitter:title"),
                ld.get('title'),
                soup.title.string if soup.title else "",
                self._extract_h1(soup)
            )

            message = first_non_empty(
                og_desc,
                meta_tags.get("twitter:description"),
                meta_tags.get("description"),
                ld.get('description'),
                self._extract_first_paragraph(soup)
            )

            image_url = first_non_empty(
                og_img,
                meta_tags.get("twitter:image"),
                meta_tags.get("twitter:image:src"),
                ld.get('image')
            )
            
            if not image_url:
                image_url = self._extract_first_image_in_article(soup)

            if image_url:
                image_url = urljoin(final_url, image_url)

            final_title = clip(plain(title), 100)
            final_message = clip(plain(message), 250)

            result = {
                "title": final_title,
                "message": final_message,
                "imageUrl": image_url
            }

            if not self._has_sufficient_meta(result):
                print(f"Postponing {article_url}: Insufficient metadata found.")
                return {"status": "awaiting_metadata", **result}

            return {"status": "success", **result}

        def _has_sufficient_meta(self, meta: dict):
            title = meta.get("title")
            message = meta.get("message")
            image_url = meta.get("imageUrl")

            if not title or title.lower() in ["new article", "untitled"]: return False
            if not message: return False
            if not image_url or not image_url.startswith(('http://', 'https://')): return False
            
            return True
        
        def _parse_json_ld(self, data):
            parsed = {}
            for item in data.get('json-ld', []):
                item_type = item.get('@type', [])
                item_type = item_type if isinstance(item_type, list) else [item_type]
                if any(t in ['Article', 'NewsArticle', 'BlogPosting'] for t in item_type):
                    parsed['title'] = item.get('headline') or item.get('name')
                    parsed['description'] = item.get('description')
                    image_node = item.get('image')
                    if isinstance(image_node, dict):
                        parsed['image'] = image_node.get('url')
                    elif isinstance(image_node, list) and image_node:
                        img = image_node[0]
                        parsed['image'] = img.get('url') if isinstance(img, dict) else img
                    else:
                        parsed['image'] = image_node
                    return parsed
            return parsed

        def _extract_h1(self, soup):
            h1 = soup.find('h1')
            return h1.get_text(strip=True) if h1 else ""

        def _extract_first_paragraph(self, soup):
            for selector in ['article', '.post-content', '#main-content', 'main']:
                container = soup.select_one(selector)
                if container:
                    p = container.find('p')
                    if p and len(p.get_text(strip=True)) > 50:
                        return p.get_text(strip=True)
            return ""

        def _extract_first_image_in_article(self, soup):
            for selector in ['article', '.post-content', '#main-content', 'main']:
                container = soup.select_one(selector)
                if container:
                    img = container.find('img')
                    if img:
                        return first_non_empty(img.get('srcset'), img.get('data-srcset'), img.get('data-src'), img.get('src'))
            return ""
    
