from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .service import YoutubeSearch  # pylint: disable=E0401


def create_app():
    app = FastAPI(
        title="QTranscribe",
        description="Transcribe audio from YouTube videos and your own audio files.",
        version="0.0.1-alpha",
    )
    yt = YoutubeSearch()

    @app.post("/api/transcribe")
    async def _(file: UploadFile = File(...)):
        return StreamingResponse(yt.from_upload(file), media_type="text/plain")  # type: ignore

    @app.get("/api/transcribe")
    def _(id: str):
        url = f"https://www.youtube.com/watch?v={id}"
        return StreamingResponse(yt.from_url(url), media_type="text/plain")  # type: ignore

    @app.get("/api/search")
    def _(query: str):
        return yt.search_videos(query)

    @app.get("/")
    def _():
        return {"message": "Qtranscribe is running!"}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
