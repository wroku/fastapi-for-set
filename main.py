from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from deta import Deta


app = FastAPI()


origins = [
    "http://set-ready-go.herokuapp.com"
    "https://set-ready-go.herokuapp.com"
    "http://localhost",
    "https://localhost",
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:3001",
    "https://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

deta = Deta("")
records = deta.Base("recordsDB")


class Record(BaseModel):
    player: str
    score: int
    time: float


@app.get("/")
def read_root():
    return {"This is simple API for SET game leaderboard"}


@app.post("/records/")
def create_record(record: Record):
    new_game = records.insert({
                "player": record.player,
                "score": record.score,
                "time": record.time
                })
    return new_game


@app.get("/records/")
def get_leaderboad(top: int = 3, avg_time_based: bool = False):
    full_leaderboard = list(records.fetch())
    if avg_time_based:
        sorted_leaderboard = sorted(full_leaderboard[0], key=lambda val: val["time"]/val["score"])
    else:
        sorted_leaderboard = sorted(full_leaderboard[0], key=lambda val: val["score"], reverse=True)

    return sorted_leaderboard[:top]


@app.put("/records/{gameId}")
def update_record(gameId: str, record: Record):
    updates = {
        "player": record.player,
        "score": record.score,
        "time": record.time
    }
    records.update(updates, gameId)

    return record
