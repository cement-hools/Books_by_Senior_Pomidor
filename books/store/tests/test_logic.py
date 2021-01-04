import os

from django.contrib.auth.models import User

from store.models import Book, UserBookRelation

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "books.settings")

from django.test import TestCase

from store.logic import operations, set_rating


class LogicTestCase(TestCase):
    def test_plus(self):
        result = operations(6, 13, '+')
        self.assertEqual(19, result)

    def test_minus(self):
        result = operations(6, 13, '-')
        self.assertEqual(-7, result)

    def test_multyply(self):
        result = operations(6, 13, '*')
        self.assertEqual(78, result)


class SetRatingTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create(username='test_username1',
                                    first_name='Ivan', last_name='Petrov')
        user2 = User.objects.create(username='test_username2',
                                    first_name='Ivan', last_name='Sidorov')
        user3 = User.objects.create(username='test_username3',
                                    first_name='1', last_name='2')

        self.book_1 = Book.objects.create(name='test book 1', price=25,
                                          author_name='Author 1', owner=user1)

        UserBookRelation.objects.create(user=user1, book=self.book_1,
                                        like=True,
                                        rate=5)
        UserBookRelation.objects.create(user=user2, book=self.book_1,
                                        like=True,
                                        rate=5)
        UserBookRelation.objects.create(user=user3, book=self.book_1,
                                        like=True,
                                        rate=4)

    def test_ok(self):
        set_rating(self.book_1)
        self.book_1.refresh_from_db()
        self.assertEqual('4.67', str(self.book_1.rating))
