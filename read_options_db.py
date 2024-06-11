import contextlib
import sqlite3
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Project:
    option: str
    state: int


class Repository(ABC):

    @abstractmethod
    def get_all(self) -> list:
        raise NotImplementedError


class PostRepository(Repository):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @contextlib.contextmanager
    def connect(self):
        with sqlite3.connect(self.db_path) as conn:
            yield conn.cursor()

    def get_all(self) -> list[Project]:
        with self.connect() as cursor:
            cursor.execute("SELECT * FROM options")
            return [Project(*post) for post in cursor.fetchall()]


def get_options() -> dict:
    repo = PostRepository("_options.db")
    return {item.option: item.state for item in repo.get_all()}

def main() -> None:
    print(get_options())

if __name__ == '__main__':
    main()




