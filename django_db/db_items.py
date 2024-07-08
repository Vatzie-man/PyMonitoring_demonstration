from abc import ABC, abstractmethod
from dataclasses import dataclass
from PyMonitoring.django_db.core import connect


@dataclass
class Project:
    id: int
    title: str
    description: str
    txt_1: str
    txt_2: str
    txt_3: str
    txt_4: str
    alert: str
    other: str


class Repository(ABC):
    @abstractmethod
    def get(self, id: int):
        raise NotImplementedError

    @abstractmethod
    def get_all(self):
        raise NotImplementedError

    @abstractmethod
    def add(self, **kwargs: object):
        raise NotImplementedError

    @abstractmethod
    def update(self, id: int, **kwargs: object):
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: int):
        raise NotImplementedError


class PostRepository(Repository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connect = connect
        self.create_table()

    def create_table(self) -> None:
        with self.connect() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS pages_project ("
                "id INTEGER PRIMARY KEY, "
                "title TEXT, "
                "description TEXT, "
                "txt_1 TEXT, "
                "txt_2 TEXT, "
                "txt_3 TEXT, "
                "txt_4 TEXT, "
                "alert TEXT, "
                "other TEXT)"
            )

    def get(self, id: int) -> Project:
        with self.connect() as cursor:
            cursor.execute("SELECT * FROM pages_project WHERE id=?", (id,))
            post = cursor.fetchone()
            if post is None:
                raise ValueError(f"Project with id {id} does not exist")
            return Project(*post)

    def get_all(self) -> list[Project]:
        with self.connect() as cursor:
            cursor.execute("SELECT * FROM pages_project")
            return [Project(*post) for post in cursor.fetchall()]

    def add(self, **kwargs: object) -> None:
        with self.connect() as cursor:
            cursor.execute(
                "INSERT INTO pages_project (title, description, txt_1, txt_2, txt_3, txt_4, alert, other) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (kwargs["title"],
                 kwargs["description"],
                 kwargs["txt_1"],
                 kwargs["txt_2"],
                 kwargs["txt_3"],
                 kwargs["txt_4"],
                 kwargs["alert"],
                 kwargs["other"]),
            )

    def update(self, id: int, **kwargs: object) -> None:
        with self.connect() as cursor:
            cursor.execute(
                "UPDATE pages_project SET title=?, description=? , txt_1=?, txt_2=?, txt_3=?, txt_4 =?, alert=?, other=? WHERE id=?",
                (kwargs["title"],
                 kwargs["description"],
                 kwargs["txt_1"],
                 kwargs["txt_2"],
                 kwargs["txt_3"],
                 kwargs["txt_4"],
                 kwargs["alert"],
                 kwargs["other"], id),
            )

    def delete(self, id: int) -> None:
        with self.connect() as cursor:
            cursor.execute("DELETE FROM pages_project WHERE id=?", (id,))
