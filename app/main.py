import logging
import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.conf import LoggingMiddleware, PrimitiveAuthorizationMiddleware, setup_logging
from app.models import Record
from app.storage import SqlLiteRecordsRepository

app = FastAPI()

env = os.getenv("ENVIRONMENT", "production")
setup_logging(env)
logger = logging.getLogger(__name__)


origins = [
    "http://localhost",
    "https://localhost",
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:3001",
    "https://localhost:3001",
]

orgins_regexes = [
    "http://34\\.96\\.4[5-8]\\.([01]?[0-9][0-9]?|2[0-4][0-9]|25[0-5])",
    "http://34\\.34\\.23[3-6]\\.([01]?[0-9][0-9]?|2[0-4][0-9]|25[0-5])"
]

app.add_middleware(PrimitiveAuthorizationMiddleware, logger=logger)
app.add_middleware(LoggingMiddleware, logger=logger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex= "|".join(orgins_regexes),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"error": "Server error", "message": "An unexpected error occurred"},
    )


records_repository = SqlLiteRecordsRepository()


@app.get("/")
def read_root():
    return {"msg": "This is simple API for SET game leaderboard"}


@app.post("/records/")
def create_record(record: Record):
    new_game: UUID = records_repository.save(record)
    return {"key": str(new_game)}


@app.get("/records/")
def get_leaderboad(top: int = 3, avg_time_based: bool = False):
    full_leaderboard: list = records_repository.fetch()
    if avg_time_based:
        # TODO correct for hints and failed noSet tries ? How it is displayed? Optimise fetching
        sorted_leaderboard = sorted(
            full_leaderboard, key=lambda val: val.time / val.score
        )
    else:
        sorted_by_time = sorted(full_leaderboard, key=lambda val: val.time)
        sorted_leaderboard = sorted(
            sorted_by_time, key=lambda val: val.score, reverse=True
        )

    return sorted_leaderboard[:top]


@app.put("/records/{gameId}")
def update_record(gameId: str, record: Record):

    current_record: Record | None = records_repository.get(UUID(gameId))
    if not current_record:
        return JSONResponse(
            status_code=404,
            content={"details": "Record not found"},
        )

    if not record.is_valid_successor(previous=current_record):
        logger.warning(
            f"Invalid update requested. {{{current_record}}} => {{{record}}}"
        )

        return JSONResponse(
            status_code=400,
            content={"details": "Invalid update."},
        )

    records_repository.update(UUID(gameId), record)
    return record
