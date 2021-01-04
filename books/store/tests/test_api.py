import json

from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count, Case, When
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.book_1 = Book.objects.create(name='test book 1', price=25,
                                          author_name='Author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='test book 2', price=55,
                                          author_name='Author 5')
        self.book_3 = Book.objects.create(name='test book Author 1', price=55,
                                          author_name='Author 3')

        UserBookRelation.objects.create(user=self.user, book=self.book_1,
                                        like=True, rate=5)

    def test_get(self):
        """Получаем список всех книг"""
        url = reverse('book-list')
        with CaptureQueriesContext(connection) as queries:  # Проверка запросов
            response = self.client.get(url)
            self.assertEqual(2, len(queries))
        books = Book.objects.all().annotate(
            annotated_likes=Count(
                Case(When(userbookrelation__like=True, then=1))),
        ).order_by('id')

        serializer_data = BookSerializer(books,
                                         many=True).data  # передаем список элементов и каждый серриализоввываем

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_get_id(self):
        """Получаем информацию об одной книге"""
        url = reverse('book-detail', args=(self.book_1.id,))
        book = Book.objects.filter(
            id__in=[self.book_1.id]).annotate(
            annotated_likes=Count(
                Case(When(userbookrelation__like=True, then=1))),
        ).first()
        response = self.client.get(url)
        serializer_data = BookSerializer(book).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_filter(self):
        """Фильтрация по цене"""
        url = reverse('book-list')
        books = Book.objects.filter(
            id__in=[self.book_2.id, self.book_3.id]).annotate(
            annotated_likes=Count(
                Case(When(userbookrelation__like=True, then=1))),
        )
        response = self.client.get(url, data={'price': 55})
        serializer_data = BookSerializer(books, many=True).data

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        """Поиск автору"""
        url = reverse('book-list')
        books = Book.objects.filter(
            id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(
                Case(When(userbookrelation__like=True, then=1))),
        )
        response = self.client.get(url, data={'search': 'Author 1'})
        serializer_data = BookSerializer(books, many=True).data

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_sort(self):
        """Сортировка по цене"""
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'price'})
        books = Book.objects.all().annotate(
            annotated_likes=Count(
                Case(When(userbookrelation__like=True, then=1))),
        ).order_by('price')
        serializer_data = BookSerializer(books, many=True).data  # передаем список элементов и каждый серриализоввываем

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        """Создание новой книги и проверка всех полей"""
        self.assertEqual(3, Book.objects.all().count())
        data = {
            "name": "Python 3",

            "price": 150,
            "author_name": "Mark Summerfield",
        }
        json_data = json.dumps(data)  # переводим словарь в json
        self.client.force_login(self.user)
        url = reverse('book-list')
        response = self.client.post(url, data=json_data,
                                    content_type='application/json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(4, Book.objects.all().count())
        new_book = Book.objects.all().last()
        self.assertEqual("Python 3", new_book.name)
        self.assertEqual(150, new_book.price)
        self.assertEqual("Mark Summerfield", new_book.author_name)

    def test_update_put(self):
        """Обновить цену"""
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 575,
            "author_name": self.book_1.author_name,
        }
        json_data = json.dumps(data)  # переводим словарь в json
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()  # замена Book.objects.get(id=self.book_1.id)
        self.assertEqual(575, self.book_1.price)

    def test_update_put_not_owner(self):
        """Не автор пытается обновить поля книги"""
        self.user2 = User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 575,
            "author_name": self.book_1.author_name,
        }
        json_data = json.dumps(data)  # переводим словарь в json
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        error = {'detail': ErrorDetail(
            string='You do not have permission to perform this action.',
            code='permission_denied')}
        self.assertEqual(error, response.data)
        self.book_1.refresh_from_db()  # замена Book.objects.get(id=self.book_1.id)
        self.assertEqual(25, self.book_1.price)

    def test_update_put_not_owner_but_staff(self):
        """Не автор но Staff обновляет поля книги"""
        self.staff_user = User.objects.create(username='test_staff_user',
                                              is_staff=True)
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 575,
            "author_name": self.book_1.author_name,
        }
        json_data = json.dumps(data)  # переводим словарь в json
        self.client.force_login(self.staff_user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()  # замена Book.objects.get(id=self.book_1.id)
        self.assertEqual(575, self.book_1.price)

    def test_update_patch(self):
        """Обновить книгу по выбранным полям"""
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": "New book's name",
            "price": 575,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(575, self.book_1.price)
        self.assertEqual("New book's name", self.book_1.name)
        self.assertEqual('Author 1', self.book_1.author_name)

    def test_delete(self):
        """Удалить книгу по id"""
        self.assertEqual(3, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        response = self.client.delete(url, )

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(2, Book.objects.all().count())

    def test_delete_not_owner(self):
        """Не автор пытается удалить книгу"""
        self.assertEqual(3, Book.objects.all().count())
        self.user2 = User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user2)
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        error = {'detail': ErrorDetail(
            string='You do not have permission to perform this action.',
            code='permission_denied')}
        self.assertEqual(error, response.data)
        self.assertEqual(3, Book.objects.all().count())


class BooksRelationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username2')
        self.book_1 = Book.objects.create(name='test book 1', price=25,
                                          author_name='Author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='test book 2', price=55,
                                          author_name='Author 5')
        self.book_3 = Book.objects.create(name='test book Author 1', price=55,
                                          author_name='Author 3')

    def test_like(self):
        """Авторизованный пользователь ставит like книге
        и добавляет в закладки"""
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            "like": True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation.like)

        data = {
            "in_bookmarks": True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        """Авторизованный пользователь ставит рейтинг книге"""
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            "rate": 3,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertEqual(3, relation.rate)

    def test_rate_wrong(self):
        """Авторизованный пользователь ставит неверный рейтинг книге"""
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            "rate": 7,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code,
                         response.data)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertEqual(None, relation.rate)
