
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def _video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc in ("youtu.be",):
        return parsed.path.strip("/")
    if parsed.netloc.endswith("youtube.com"):
        q = parse_qs(parsed.query)
        return q.get("v", [""])[0]
    return url  # assume already id

def fetch_transcript(url: str, languages=("de", "de-DE", "en")) -> str:
    vid = _video_id(url)
    transcript = YouTubeTranscriptApi.get_transcript(vid, languages=list(languages))
    return " ".join(chunk["text"] for chunk in transcript if chunk.get("text"))
