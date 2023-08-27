import uvicorn
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware

from my_contacts.database.db_connect import get_db
from my_contacts.routes import contacts, auth, users

app = FastAPI()


app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(users.router, prefix="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    redis_cache = await redis.Redis(host="localhost", port=6379, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_cache)


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error connecting to the database")


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", port=8000, reload=True, log_level="info")
