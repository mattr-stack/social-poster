import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Extract metadata from URLs"""

    def extract_metadata(self, url: str) -> dict[str, str]:
        """Extract title, description, and image from URL"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            metadata = {
                'title': self._get_title(soup),
                'description': self._get_description(soup),
                'image': self._get_image(soup, url),
                'url': url,
                'keywords': self._get_keywords(soup)
            }

            logger.info(f"Extracted metadata for {url}: {metadata['title']}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to extract metadata from {url}: {str(e)}")
            return {'title': '', 'description': '', 'image': '', 'url': url, 'keywords': []}

    def _get_title(self, soup) -> str:
        """Extract page title"""
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')

        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title:
            return twitter_title.get('content', '')

        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        return ''

    def _get_description(self, soup) -> str:
        """Extract page description"""
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '')

        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc:
            return twitter_desc.get('content', '')

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')

        return ''

    def _get_image(self, soup, base_url: str) -> str:
        """Extract page image"""
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_url = og_image.get('content', '')
            return self._resolve_url(img_url, base_url)

        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image:
            img_url = twitter_image.get('content', '')
            return self._resolve_url(img_url, base_url)

        return ''

    def _get_keywords(self, soup) -> list[str]:
        """Extract page keywords"""
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            keywords = keywords_meta.get('content', '')
            return [keyword.strip() for keyword in keywords.split(',')]
        return []

    def _resolve_url(self, url: str, base_url: str) -> str:
        """Resolve relative URLs"""
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return urljoin(base_url, url)
        return url
