import os
from fastapi import FastAPI

app = FastAPI()

print(os.environ.get('DB_SQLITE'))


@app.get("/")
async def root():
    return {"message": "Hello World"}