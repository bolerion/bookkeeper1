"""
Модель бюджета
Должны быть следующие поля:
срок
категория расходов
сумма
"""
import datetime
from dataclasses import dataclass
from datetime import date, timedelta
from bookkeeper.repository.abstract_repository import AbstractRepository
from bookkeeper.models.category import Category
from bookkeeper.models.expense import Expense

@dataclass
class Budget:
    period: str
    amount: int
    budget: int
    pk: int = 0

    def calculate(self, repo: AbstractRepository['Expense']) -> int:
        """посчитать сумму расходов за период

        repo - репозиторий расходов

        exp - сумма расходов за период
        """
        delta = timedelta(days = 0)
        if self.period == 'День':
            delta = timedelta(days = 1)
        if self.period == 'Неделя':
            delta = timedelta(weeks = 7)
        if self.period == 'Месяц':
            delta = timedelta(days=30)

        start_date = date.today() - delta
        end_date = date.today()
        expenses = repo.get_all(where={'expense_date':(start_date, end_date)})
        exp = 0
        for expense in expenses:
            self.amount += expense.amount
        return self.amount


