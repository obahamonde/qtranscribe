from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .service import YoutubeSearch
from .schema import YoutubeVideo

def create_app():
	app = FastAPI(
		title="QTranscribe",
		description="Transcribe audio from YouTube videos and your own audio files.",
		version="0.1.0",
	)
	yt = YoutubeSearch()

	@app.post("/api/transcribe", response_class=StreamingResponse)
	async def _(file: UploadFile = File(...)):
		return StreamingResponse(await yt.from_upload(file), media_type="text/plain")

	@app.get("/api/transcribe", response_class=StreamingResponse)
	def _(url: str):
		return StreamingResponse(yt.transcribe(url), media_type="text/plain")

	@app.get("/api/search", response_model=list[YoutubeVideo])	
	def _(query: str):
		return yt.search_videos(query)

	return app