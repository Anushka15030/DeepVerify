from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse


app = FastAPI(title="DeepVerify MinerU Service")


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "mineru",
        "python": sys.version,
    }


@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are supported"},
        )

    input_path = UPLOAD_DIR / file.filename
    document_name = Path(file.filename).stem
    output_path = OUTPUT_DIR / document_name

    with open(input_path, "wb") as f:
        f.write(await file.read())

    command = [
        "mineru",
        "-p",
        str(input_path),
        "-o",
        str(output_path),
        "-b",
        "pipeline",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return JSONResponse(
            status_code=500,
            content={
                "error": "MinerU processing failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    return {
        "status": "completed",
        "document": document_name,
        "output_directory": str(output_path),
        "stdout": result.stdout,
    }