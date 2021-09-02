import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.com_form = CommentForm
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='/posts/small.gif/',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст поста 1',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.post_to_create = {
            'text': 'Текст поста',
            'group': cls.group.id,
        }
        cls.post_after_edit = {
            'text': 'Текст поста после изменения',
            'group': cls.group.id,
        }
        cls.comment = {
            'text': 'Текст комментария',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.post_to_create,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.post_to_create['text'],
                group=self.post_to_create['group'],
                author=self.user,
                image=self.uploaded,
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма корректно меняет запись в Post."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    args=[self.post.id]
                    ),
            data=self.post_after_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[self.post.id])
        )
        self.assertEqual(Post.objects.count(), posts_count)

        post_edit = Post.objects.filter(
            text=self.post_after_edit['text'],
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        self.assertTrue(post_edit.exists())

    def test_comment_create(self):
        """Валидная форма создает комментарий"""
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=self.comment,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[self.post.id])
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=self.comment['text']
            ).exists()
        )
