from typing_extensions import Required, TypedDict


class YoutubeVideo(TypedDict, total=False):
    title: str
    url: str
    length: int
    views: int
    author: str
    embed_url: str


class WhisperTranscription(TypedDict, total=False):
    text: Required[str]
