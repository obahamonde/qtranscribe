from typing_extensions import TypedDict

class YoutubeVideo(TypedDict, total=False):
    title: str
    url: str
    length: int
    views: int
    author: str
    embed_url: str

