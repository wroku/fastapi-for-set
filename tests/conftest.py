import sqlite3
from fastapi import FastAPI
from fastapi.middleware import Middleware
from pytest import fixture

from app.storage import SqlLiteRecordsRepository


@fixture(autouse=True)
def with_test_db(monkeypatch):
    monkeypatch.setattr("app.storage.SqlLiteRecordsRepository.DB_NAME", 'test.db')

@fixture(autouse=True)
def with_test_db(monkeypatch):
    monkeypatch.setattr("app.storage.SqlLiteRecordsRepository.DB_NAME", 'test.db')


@fixture
def setup_db(with_test_db):
    repo = SqlLiteRecordsRepository()
    yield
    con = sqlite3.connect(repo.DB_NAME)
    sql = f"DELETE from {repo.TABLE_NAME}"
    con.execute(sql)
    con.commit()
    con.close()    

def remove_middleware(app: FastAPI, target: str) -> FastAPI:
    new_middlewares: list[Middleware] = []
    for middleware in app.user_middleware:
        if not middleware.cls.__name__ == target:
            new_middlewares.append(middleware)
    app.user_middleware = new_middlewares
    app.middleware_stack = app.build_middleware_stack()
    return app