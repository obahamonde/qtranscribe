import re
import tempfile
from functools import cached_property
from typing import Generator, Any

import numpy as np
import pydub  # type: ignore
import pytube  # type: ignore
import torch
from httpx import get
from whisper import load_model, transcribe  # type: ignore

from .schemas import WhisperTranscription, YoutubeVideo

SAMPLE_RATE = 16000
CHUNK_DURATION = 30
CHUNKSIZE = CHUNK_DURATION * SAMPLE_RATE
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class YoutubeSearch:

    @cached_property
    def model(self):
        return load_model("small").to(DEVICE)

    def from_url(self, url: str) -> Generator[str, None, None]:
        yt = pytube.YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()  # type: ignore
        with tempfile.TemporaryDirectory() as tmpdir:
            stream.download(output_path=tmpdir)  # type: ignore
            audio_file_path = f"{tmpdir}/{stream.default_filename}"  # type: ignore
            audio = pydub.AudioSegment.from_file(audio_file_path)  # type: ignore
            audio = audio.set_channels(1).set_frame_rate(SAMPLE_RATE)  # type: ignore
            audio_samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / (  # type: ignore
                2**15
            )
            for i in range(0, len(audio_samples), CHUNKSIZE):
                chunk = audio_samples[i : i + CHUNKSIZE]
                if len(chunk) < CHUNKSIZE:
                    chunk = np.pad(chunk, (0, CHUNKSIZE - len(chunk)), mode="constant")
                else:
                    chunk = np.array(chunk)
                    yield self.transcribe(chunk)

    def _search_videos(self, query: str):
        search_url = f"https://www.youtube.com/results?search_query={query}"
        response = get(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            },
        )
        data = response.text
        pattern = re.compile(r"watch\?v=(\S{11})")
        video_ids = pattern.findall(data)
        videos = set[str](video_ids)
        for video in videos:
            yt_vid = pytube.YouTube(video)
            yield YoutubeVideo(
                {
                    "title": yt_vid.title,
                    "url": video,
                    "length": yt_vid.length,
                    "views": yt_vid.views,
                    "author": yt_vid.author,
                    "embed_url": yt_vid.embed_url,
                }
            )

    def search_videos(self, query: str):
        return list(self._search_videos(query))

    def transcribe(self, chunk: np.ndarray[np.float32, Any]) -> str:
        data_dict: WhisperTranscription = transcribe(
            model=self.model, audio=torch.from_numpy(chunk), verbose=True  # type: ignore
        )  # type: ignore
        return data_dict["text"]
