from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from app.database import Base, engine
from app.routers import upload, documents, analysis
from app.indexer import get_index

# Загружаем TF-IDF индекс при старте приложения
_index = get_index()
if _index.load():
    print(f"✅ TF-IDF индекс загружен: {_index.n_texts} текстов (построен {_index.built_at})")
else:
    print("⚠️ TF-IDF индекс не найден. Запустите: python build_index.py")


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plagiarism & AI Detector",
    description="API для проверки текстов на плагиат и использование ИИ",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])

@app.get("/health")
async def health():
    return {"status": "healthy"}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

FRONTEND_DIR = "/home/server/plagiarism-detector/frontend"

# Раздача статики
app.mount("/css", StaticFiles(directory=f"{FRONTEND_DIR}/css"), name="css")
app.mount("/js", StaticFiles(directory=f"{FRONTEND_DIR}/js"), name="js")

# Главная страница
@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(f"{FRONTEND_DIR}/index.html")

# favicon
@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    return FileResponse(f"{FRONTEND_DIR}/favicon.ico")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
