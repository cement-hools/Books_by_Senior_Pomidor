from django.db.models import Avg

from store.models import UserBookRelation


def operations(a, b, c):
    if c == '+':
        return a + b
    if c == '-':
        return a - b
    if c == '*':
        return a * b


def set_rating(book):
    rating = UserBookRelation.objects.filter(book=book).aggregate(
        rating=Avg('rate')).get('rating')
    book.rating = rating
    book.save()
