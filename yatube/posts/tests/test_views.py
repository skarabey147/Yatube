import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='author')
        cls.author_2 = User.objects.create_user(username='author_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='/posts/small.jpg/',
            content=test_image,
            content_type='image/jpg'
        )
        cls.author_post = Post.objects.create(
            text='Текст поста автора',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            text='Текст коммента',
            author=cls.user,
            post=cls.post,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        group_slug = PostViewTest.group.slug
        user_username = PostViewTest.user.username
        post_id = PostViewTest.post.id
        templates_names = {
            'posts/index.html': (reverse('posts:index'),),
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={'slug': group_slug}),
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': user_username}),
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': post_id}),
            ),
            'posts/create_post.html': (
                reverse('posts:post_create'),
                reverse('posts:post_edit', kwargs={'post_id': post_id}),
            ),
        }
        for template, reverse_names in templates_names.items():
            for reverse_name in reverse_names:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def _post_for_tests(self, context, some_posts):
        self.assertEqual(context.text, some_posts.text)
        self.assertEqual(context.group, some_posts.group)
        self.assertEqual(context.author, some_posts.author)
        self.assertEqual(context.image, PostViewTest.uploaded)

    def test_index(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        first_object = response.context['page_obj'][0]
        all_posts = Post.objects.all()[0]
        self._post_for_tests(first_object, all_posts)

    def test_group_list(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group = PostViewTest.group
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': group.slug})
        )
        first_object = response.context['page_obj'][0]
        post_of_group = group.posts.all()[0]
        self._post_for_tests(first_object, post_of_group)

    def test_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        author = PostViewTest.user
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['page_obj'][0]
        post_of_author = author.posts.all()[0]
        self._post_for_tests(first_object, post_of_author)

    def test_post_detail(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewTest.post.id})
        )

        self.assertEqual(response.context['post'], self.post)

        post_title = self.post.text[:30]
        self.assertEqual(response.context['post'].text, post_title)

        post_count = Post.objects.filter(author=self.post.author).count()
        self.assertEqual(
            response.context['post'].author.posts.count(), post_count
        )

    def test_create_post(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post = PostViewTest.post
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id})
        )

        form_fields = {
            'text': (forms.fields.CharField, post.text),
            'group': (forms.fields.ChoiceField, post.group.id),
            'image': (forms.fields.ImageField, post.image)

        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_new_post(self):
        """Тест создания нового поста"""
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        index_count = Post.objects.count()
        group_count = Post.objects.filter(group=new_post.group).count()
        usercount = Post.objects.filter(author=new_post.author).count()
        template_name = {
            reverse('posts:index'): index_count,
            reverse('posts:group_posts',
                    kwargs={'slug': new_post.group.slug}): group_count,
            reverse('posts:profile',
                    kwargs={'username': new_post.author.username}): usercount,
        }
        for reverse_name, count in template_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)

    def test_create_new_comment(self):
        """Тест создания нового комментария"""
        comment_count = Comment.objects.count()
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewTest.post.id})
        )
        self.assertEqual(len(response.context['comments']), comment_count)

    def test_follow_page(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        followed = Follow.objects.filter(user=self.user).values('author')
        post_from_follow = Post.objects.filter(author__in=followed)
        self._post_for_tests(first_object, post_from_follow[0])

    def test_user_follow(self):
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author_2})
        )
        follow_count_2 = Follow.objects.count()
        self.assertEqual(follow_count_2, follow_count + 1)

    def test_user_unfollow(self):
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        follow_count_2 = Follow.objects.count()
        self.assertEqual(follow_count_2, follow_count - 1)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(1, 15):
            Post.objects.create(
                text=f'Пост номер {i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        template = {
            reverse('posts:index'): 10,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): 10,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): 10,
        }
        for reverse_name, count in template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), count)

    def test_second_page_contains_four_records(self):
        template = {
            reverse('posts:index'): 4,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): 4,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): 4,
        }
        for reverse_name, count in template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name + '?page=2'
                )
                self.assertEqual(len(response.context['page_obj']), count)
