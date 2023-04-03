from datetime import datetime
from inspect import get_annotations
import sqlite3
from bookkeeper.repository.abstract_repository import AbstractRepository, T


class SQLiteRepository(AbstractRepository[T]):

    db_file: str #название файла репозитория
    cls: type #данные для хранения
    table_name: str #название таблички
    fields: dict[str, any] #поля таблички

    def __init__(self, db_file: str, cls: type) -> None:
        self.db_file = db_file
        self.cls = cls
        self.table_name = cls.__name__
        self.fields = get_annotations(cls, eval_str=True) #словарь
        self.fields.pop('pk')


        with sqlite3.connect(self.db_file) as con:
            cursorobj = con.cursor()
            res = cursorobj.execute('SELECT name FROM sqlite_master')
            db_tables = [t[0].lower() for t in res.fetchall()]
            if self.table_name not in db_tables:
                col_names = ', '.join(self.fields.keys())
                q = f'CREATE TABLE IF NOT EXISTS {self.table_name} (' \
                    f'"pk" INTEGER PRIMARY KEY AUTOINCREMENT, {col_names})'
                cursorobj.execute(q)
        con.close()

    def __generate_object(self, db_row: tuple) -> T:
        obj = self.cls(self.fields)
        for field, value in zip(self.fields, db_row[1:]):
            setattr(obj, field, value)
        obj.pk = db_row[0]
        return obj

    def add(self, obj: T) -> int:
        """
        Добавить объект в репозиторий, вернуть id объекта,
        также записать id в атрибут pk.
        """
        names = ', '.join(self.fields.keys())
        p = ', '.join("?" * len(self.fields))
        values = [getattr(obj, x) for x in self.fields]
        with sqlite3.connect(self.db_file) as con:
            cursorobj = con.cursor()
            cursorobj.execute('PRAGMA foreign_keys = ON')
            cursorobj.execute(f'INSERT INTO {self.table_name} ({names}) VALUES ({p})', values)
            obj.pk = cursorobj.lastrowid
        con.close()
        return obj.pk


    def get(self, pk: int) -> T | None:
        """Получить объект по id"""
        with sqlite3.connect(self.db_file) as con:
            cursorobj = con.cursor()
            cursorobj.execute('PRAGMA foreign_keys = ON')
            cursorobj.execute(f'SELECT * FROM {self.table_name} WHERE pk = {pk}')
            row = cursorobj.fetchone() #извлекает следующую строку из набора результатов запроса, возвращает кортеж
        con.close()

        if row is None:
            return None

        return self.__generate_object(row) #вернули объект по айдишнику


    def get_all(self, where: dict[str, any] | None = None):
        """
        Получить все записи по некоторому условию
        where - условие в виде словаря {'название_поля': значение}
        если условие не задано (по умолчанию), вернуть все записи
        """
        with sqlite3.connect(self.db_file) as con:
            cursorobj = con.cursor()
            if where is None:
                cursorobj.execute(f'SELECT * FROM {self.table_name}')
            else:
                q = ' AND'.join([f'{key} = "{value}"' for key, value in where.items()])
                cursorobj.execute(f'SELECT * FROM {self.table_name} WHERE {q}')

            rows = cursorobj.fetchall()
        con.close()

        if rows:
            return [self.__generate_object(row) for row in rows]
        else:
            return []

    def update(self, obj: T):
        """ Обновить данные об объекте. Объект должен содержать поле pk. """
        names = list(self.fields.keys())
        sets = ', '.join(f'{name} = {getattr(obj, name)}' for name in names)
        with sqlite3.connect(self.db_file) as con:
            cursorobj = con.cursor()
            cursorobj.execute('PRAGMA foreign_keys = ON')
            cursorobj.execute(f'UPDATE {self.table_name} SET {sets} WHERE pk = {obj.pk}')
        con.close()

    def delete(self, pk: int):
        """ Удалить запись """
        with sqlite3.connect(self.db_file) as con:
            cursorobj = con.cursor()
            cursorobj.execute('PRAGMA foreign_keys = ON')
            cursorobj.execute(f'DELETE FROM {self.table_name} WHERE pk = {pk}')
        con.close()


