import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )

    @classmethod
    def tearDownClass(cls):
        """Удаляем тестовые медиа."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostFormsTests.author)
        self.post = Post.objects.create(
            author=PostFormsTests.author,
            text='Тестовый пост',
            group=PostFormsTests.group
        )

    def test_create_form(self):
        """Проверяем создание поста при отправке формы create"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': PostFormsTests.group.pk,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={
                    'username': PostFormsTests.author.username
                }
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        testing_post = Post.objects.first()
        self.assertEqual(testing_post.text, form_data['text'])
        self.assertEqual(testing_post.image, 'posts/small.gif')
        self.assertEqual(testing_post.group.pk, form_data['group'])

    def test_edit_form(self):
        """Проверяем редактирование поста при отправке формы edit"""
        posts_count = Post.objects.count()
        new_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='new.gif',
            content=new_gif,
            content_type='image/gif'
        )
        new_group = Group.objects.create(
            title='Тестовая группа два',
            slug='test-slug-2',
            description='Тестовое описание группы два',
        )
        form_data = {
            'text': 'измененный пост',
            'group': new_group.pk,
            'image': uploaded,
        }
        old_text = self.post.text
        old_group = PostFormsTests.group
        response = self.author_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        testing_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(testing_post.text, form_data['text'])
        self.assertEqual(testing_post.image, 'posts/new.gif')
        self.assertEqual(testing_post.group.pk, form_data['group'])
        # Тут не понял. Логика редактирования поста в том, что-бы
        # изменить данные в посте, а post.pk не должен меняться.
        # Т.е. со старой страницы он никуда не должен исчезать.
        # Добавил проверки на то, что старые данные не совпадают
        # с новыми и группу еще заодно новую добавил, хотя смысла
        # в этом не вижу. Прокомментируйте пожалуйста.
        self.assertNotEqual(testing_post.text, old_text)
        self.assertNotEqual(testing_post.group, old_group)

    def test_create_comment(self):
        """Проверяем создание комментария при отправке формы"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий'
        }
        response = self.author_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.pk
                }
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        testing_comment = Comment.objects.first()
        self.assertEqual(testing_comment.text, form_data['text'])
        # Какие группы? Не вижу взаимосвязи комментариев и групп. Тут же
        # только пост, автор поста и "комментатор". Проверить что группа
        # не изменилась после добавления комментария? Ок...
        # Будьте добры, объясните, вероятно я что-то не понимаю.
        self.assertEqual(testing_comment.author, PostFormsTests.author)
        self.assertEqual(testing_comment.post.group, PostFormsTests.group)
