from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book
from store.serializers import BookSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.book_1 = Book.objects.create(name='test book 1', price=25,
                                          author_name='Author 1')
        self.book_2 = Book.objects.create(name='test book 2', price=55,
                                          author_name='Author 5')
        self.book_3 = Book.objects.create(name='test book Author 1', price=55,
                                          author_name='Author 3')

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        serializer_data = BookSerializer([self.book_1, self.book_2,
                                          self.book_3], many=True).data # передаем список элементов и каждый серриализоввываем

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'price': 55})
        serializer_data = BookSerializer([self.book_2,
                                          self.book_3], many=True).data # передаем список элементов и каждый серриализоввываем

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        serializer_data = BookSerializer([self.book_1,
                                          self.book_3], many=True).data # передаем список элементов и каждый серриализоввываем

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_sort(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'price'})
        serializer_data = BookSerializer([self.book_1, self.book_2,
                                          self.book_3], many=True).data # передаем список элементов и каждый серриализоввываем

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
