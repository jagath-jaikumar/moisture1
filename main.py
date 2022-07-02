from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"app": "moisture1"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=os.getenv("PORT", default=5000),
        log_level="info",
    )
