from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "teruterubozu server running"}
