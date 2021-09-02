from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста!',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.user)

    def test_all_urls_for_guest(self):
        """Тестируем страницы для гостя"""
        urls = {
            '/': HTTPStatus.OK.value,
            f'/group/{self.group.slug}/': HTTPStatus.OK.value,
            f'/profile/{self.user}/': HTTPStatus.OK.value,
            f'/posts/{self.post.id}/': HTTPStatus.OK.value,
            '/unexisting_page/': HTTPStatus.NOT_FOUND.value
        }
        for adress, status_code in urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_post_create_for_authorized_user(self):
        """
        Тестируем страницу создания поста для
        авторизованного пользователя
        """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_edit_for_author(self):
        """
        Тестируем страницу редактирования поста,
        для автора поста
        """
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_templates_for_all_urls(self):
        """Проверка соответствия шаблонов для url"""
        urls = {
            'posts/index.html': ('/',),
            'posts/group_list.html': (f'/group/{self.group.slug}/',),
            'posts/profile.html': (f'/profile/{self.user}/',),
            'posts/post_detail.html': (f'/posts/{self.post.id}/',),
            'posts/create_post.html': ('/create/',
                                       f'/posts/{self.post.id}/edit/',),
            'posts/follow.html': ('/follow/',),
        }
        for template, addresses in urls.items():
            for adress in addresses:
                with self.subTest(adress=adress):
                    response = self.author_client.get(adress)
                    self.assertTemplateUsed(response, template)
