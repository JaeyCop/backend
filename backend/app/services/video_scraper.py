import logging
import re
import urllib.parse
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class VideoScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_youtube_videos(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Get YouTube videos for a recipe query."""
        try:
            search_query = f"{query} recipe cooking tutorial"
            yt_search = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(search_query)

            response = requests.get(yt_search, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            videos = []
            script_tags = soup.find_all("script")

            for script in script_tags:
                if "var ytInitialData" in str(script):
                    script_content = str(script)
                    # Extract video data from YouTube's initial data
                    try:
                        # Simple regex to find video IDs and titles
                        video_pattern = r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"'
                        matches = re.findall(video_pattern, script_content)

                        for video_id, title in matches[:max_results]:
                            if len(videos) >= max_results:
                                break
                            videos.append({
                                "title": title,
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                            })
                    except:
                        pass
                    break

            # Fallback method - look for video links
            if not videos:
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if "/watch?v=" in href and len(videos) < max_results:
                        title = link.get("title", "Recipe Video")
                        video_url = "https://www.youtube.com" + href
                        videos.append({
                            "title": title,
                            "url": video_url,
                            "thumbnail": None
                        })

            return videos

        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {e}")
            return []

    def get_single_youtube_link(self, query: str) -> Optional[str]:
        """Get a single YouTube video link for a recipe."""
        videos = self.get_youtube_videos(query, max_results=1)
        return videos[0]["url"] if videos else None


video_scraper = VideoScraper()
