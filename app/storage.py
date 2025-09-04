import abc
import logging
import sqlite3
from uuid import UUID, uuid4

from app.models import Record

logger = logging.getLogger(__name__)


class RecordsRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, game_id: UUID) -> Record | None:
        pass

    @abc.abstractmethod
    def save(self, record: Record) -> UUID:
        pass

    @abc.abstractmethod
    def update(self, game_id: UUID, record: Record) -> UUID | None:
        pass

    @abc.abstractmethod
    def fetch(self) -> list[Record]:
        pass


class InMemoryRecordsRepository(RecordsRepository):
    def __init__(self):
        self.storage: dict[str, dict] = {}
        super().__init__()

    def get(self, game_id: UUID) -> Record | None:
        record_data = self.storage[str(game_id)]
        if record_data:
            return Record(**record_data)

    def save(self, record: Record) -> UUID:
        id: UUID = uuid4()
        self.storage[str(id)] = record.model_dump()
        return id

    def update(self, game_id: UUID, record: Record) -> UUID | None:
        instance = self.storage.get(str(game_id))
        if instance:
            self.storage[str(game_id)] = record.model_dump()
            return game_id

    def fetch(self) -> list[Record]:
        return [Record(**val) for val in self.storage.values()]


class SqlLiteRecordsRepository(RecordsRepository):
    DB_NAME: str = "leaderboard.db"
    TABLE_NAME: str = "records"
    CREATE_SQL: str = f"""CREATE TABLE {TABLE_NAME} (
                        id TEXT PRIMARY KEY,
                        player_name text NOT NULL, 
                        score int NOT NULL, 
                        time float NOT NULL
                        )"""

    def __init__(self):
        con = sqlite3.connect(self.DB_NAME)
        res = con.execute(
            "SELECT name FROM sqlite_master WHERE tbl_name=?", (self.TABLE_NAME,)
        )
        if not res.fetchone():
            con.execute(self.CREATE_SQL)
            con.commit()
        super().__init__()

    def get(self, game_id: UUID) -> Record | None:
        con = sqlite3.connect(self.DB_NAME)
        sql: str = f"SELECT * from {self.TABLE_NAME} WHERE id = ?"
        res = con.execute(sql, (str(game_id),))
        record_data: tuple = res.fetchone()[1:]

        if record_data:
            return Record.from_tuple(record_data)

    def save(self, record: Record) -> UUID:
        game_id: UUID = uuid4()
        con = sqlite3.connect(self.DB_NAME)
        sql = f"INSERT INTO {self.TABLE_NAME} VALUES(?, ?, ?, ?) returning id"
        res = con.execute(sql, (str(game_id), record.player, record.score, record.time))
        res.fetchall()
        con.commit()

        return game_id

    def update(self, game_id: UUID, record: Record) -> UUID | None:
        con = sqlite3.connect(self.DB_NAME)
        sql = f"""UPDATE {self.TABLE_NAME} 
                  SET player_name = ?,
                      score = ?,
                      time = ? 
                  WHERE id = ?"""
        
        params: tuple = tuple(val for val in record.model_dump().values()) + (
            str(game_id),
        )

        con.execute(sql, params)
        con.commit()

        return game_id

    def fetch(self) -> list[Record]:
        con = sqlite3.connect(self.DB_NAME)
        sql = f"SELECT * from {self.TABLE_NAME}"
        res = con.execute(sql)
        return [Record.from_tuple(record_tuple[1:]) for record_tuple in res.fetchall()]
