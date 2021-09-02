from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class TestCacheIndex(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('Noname')
        cls.post = Post.objects.create(
            text='Пост для кэша',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()

    def get_response(self):
        return self.guest_client.get(reverse('posts:index'))

    def test_cache(self):
        """Тестируем кеширование страницы index"""
        response = self.get_response()
        self.assertContains(response, self.post.text, status_code=200)

        self.post.delete()
        self.assertContains(response, self.post.text, status_code=200)

        cache.clear()
        new_response = self.get_response()
        self.assertNotContains(new_response, self.post.text, status_code=200)
