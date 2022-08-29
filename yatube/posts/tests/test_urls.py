from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class PostStaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        """Posts: проверяем код ответа главной страницы."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.public_templates_urls = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test_name/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        cls.private_templates_urls = {
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_name_two')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_response_code_guest(self):
        """Проверяем коды ответа неавторизованного пользователя."""
        for address in self.public_templates_urls.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            self.guest_client.get(
                '/unexisting_page/'
            ).status_code, HTTPStatus.NOT_FOUND
        )

    def test_response_code_private(self):
        """Проверяем коды ответа зарегистрированного пользователя."""
        for address in self.private_templates_urls.keys():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest(self):
        """Проверяем редиректы неавторизованного пользователя."""
        templates_url_names = {
            '/posts/1/edit/': '/posts/1/',
            '/create/': '/auth/login/?next=/create/',
        }
        for address, answer in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, answer)

    def test_redirect_user(self):
        """Проверяем редирект пользователя c /posts/<post_id>/edit/."""
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            **self.public_templates_urls, **self.private_templates_urls
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
