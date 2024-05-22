import re
import tempfile
from typing import Generator

import numpy as np
import pydub
import pytube
import torch
from requests import get
from whisper import load_model, transcribe
from fastapi import UploadFile
from .schema import YoutubeVideo

SAMPLE_RATE = 16000
CHUNK_DURATION = 3
CHUNKSIZE = SAMPLE_RATE * CHUNK_DURATION
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = load_model("medium").to(DEVICE)





class YoutubeSearch:
	async def from_url(self,url:str ):
		yt = pytube.YouTube(url)
		stream = yt.streams.filter(only_audio=True).first()
		with tempfile.TemporaryDirectory() as tmpdir:
			stream.download(output_path=tmpdir)
			audio_file_path = f"{tmpdir}/{stream.default_filename}"
			audio = pydub.AudioSegment.from_file(audio_file_path)
			audio = audio.set_channels(1).set_frame_rate(SAMPLE_RATE)
			audio_samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / (
				2**15
			)
			for i in range(0, len(audio_samples), CHUNKSIZE):
				chunk = audio_samples[i : i + CHUNKSIZE]
				if len(chunk) < CHUNKSIZE:
					chunk = np.pad(chunk, (0, CHUNKSIZE - len(chunk)), mode="constant")
				text = transcribe(model, chunk)
				assert "text" in text
				yield text["text"]

	def _search_videos(self, query: str) -> Generator[YoutubeVideo, None, None]:
		search_url = f"https://www.youtube.com/results?search_query={query}"
		response = get(
			search_url,
			headers={
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
			},
		)
		data = response.text
		pattern = re.compile(r"watch\?v=(\S{11})")
		videos = set[str]()
		for video_id in pattern.findall(data):
			videos.add(f"https://www.youtube.com/watch?v={video_id}")
		for video in videos:
			yt_vid = pytube.YouTube(video)
			yield {
				"title": yt_vid.title,
				"url": video,
				"length": yt_vid.length,
				"views": yt_vid.views,
				"author": yt_vid.author,
				"embed_url": yt_vid.embed_url
			}

	def search_videos(self, query: str) -> list[YoutubeVideo]:
		return list(search_videos(query))

	async def from_upload(self, file: UploadFile) -> str:
		with tempfile.TemporaryDirectory() as tmpdir:
			file_path = f"{tmpdir}/{file.filename}"
			with open(file_path, "wb") as f:
				f.write(await file.read())
			audio = pydub.AudioSegment.from_file(file_path)
			audio = audio.set_channels(1).set_frame_rate(SAMPLE_RATE)
			audio_samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / (2**15)
			for i in range(0, len(audio_samples), CHUNKSIZE):
				chunk = audio_samples[i : i + CHUNKSIZE]
				if len(chunk) < CHUNKSIZE:
					chunk = np.pad(chunk, (0, CHUNKSIZE - len(chunk)), mode="constant")
				text = transcribe(model, chunk)
				assert "text" in text
				yield text["text"]
