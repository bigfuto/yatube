import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from http import HTTPStatus
from django.core.cache import cache

from ..models import Post, Group, Follow


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT, )
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Вторая тестовая группа',
            slug='test-slug-two',
            description='Тестовое описание второй группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_name_two')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostViewsTests.author)
        cache.clear()

    def test_uses_correct_template(self):
        """URL-адреса используют правильные шаблоны."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.pk
                }
            ): 'posts/create_post.html'
        }
        for address, answer in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, answer)

    def test_forms(self):
        """Проверяем шаблоны post_create и post_edit"""
        form_list = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for form in form_list:
            with self.subTest(form=form):
                for field, answer in form_fields.items():
                    with self.subTest(field=field):
                        response = self.author_client.get(form).context
                        self.assertIsInstance(
                            response['form'].fields[field], answer
                        )

    def test_pages_context(self):
        """Проверяем context в index, group_posts, profile и post_detail"""
        templates_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ),
        ]
        for page in templates_list:
            with self.subTest(page=page):
                if 'page_obj' in self.author_client.get(page).context:
                    cache.clear()
                    response = (
                        self.author_client.get(page).context['page_obj'][0]
                    )
                else:
                    response = self.author_client.get(page).context['post']
                cache.clear()
                self.assertEqual(response.author, self.author)
                self.assertEqual(response.text, self.post.text)
                self.assertEqual(response.group, self.post.group)
                self.assertEqual(response.image, self.post.image)

    def test_post_not_own_group(self):
        """Проверяем отсутствие поста в другой группе"""
        tempate_page = reverse(
            'posts:group_list',
            kwargs={'slug': self.group2.slug}
        )
        response = self.authorized_client.get(tempate_page).context
        self.assertEqual(len(response['page_obj']), 0)

    def test_follow(self):
        """Проверяем подпичку на автора."""
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewsTests.author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author, PostViewsTests.author)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """Проверяем отписку от автора."""
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewsTests.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostViewsTests.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_post_following(self):
        """
        Проверяем появление поста в ленте подписчика
        и отсутствие у пользоватля без подписки.
        """
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewsTests.author.username}
            )
        )
        response_following = self.authorized_client.get(
            reverse('posts:follow_index')
        ).context
        self.assertEqual(len(response_following['page_obj']), follow_count + 1)
        response_author = self.author_client.get(
            reverse('posts:follow_index')
        ).context
        self.assertEqual(len(response_author['page_obj']), follow_count)


class PostViewsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание шруппы',
        )
        # Премного благодарствую. Выветрили из моей головы дезинформацию.
        # Я почему-то представлял, что в тестах используется какая-то
        # виртуальная БД которая не совсем БД а скорее фикстуро-БД.
        # И даже не рассматривал вариант обращения к базе данных)
        # Теперь понятно, все разложилось по полочкам!
        cls.posts = [Post(
            author=cls.author,
            text='Тестовый пост' + str(post_num),
            group=cls.group,
        ) for post_num in range(
            settings.POSTS_PER_PAGE + settings.POSTS_PER_PAGE // 2
        )]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_paginator(self):
        """Проверяем paginator в index, group_posts и profile"""
        tempate_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        ]
        for page in tempate_pages:
            with self.subTest(page=page):
                response = self.author_client.get(page).context
                self.assertEqual(
                    len(response['page_obj']), settings.POSTS_PER_PAGE
                )
                response = self.author_client.get(page + '?page=2').context
                self.assertEqual(
                    len(response['page_obj']),
                    settings.POSTS_PER_PAGE // 2
                )


class PostViewsCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание шруппы',
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PostViewsCacheTests.author)
        self.post = Post.objects.create(
            author=PostViewsCacheTests.author,
            text='Тестовый пост',
            group=PostViewsCacheTests.group
        )

    def test_cache(self):
        """Проверяем cache для index"""
        pages = reverse('posts:index')
        response = self.author_client.get(pages).content
        self.post.delete()
        response_cache = self.author_client.get(pages).content
        self.assertEqual(response_cache, response)
        cache.clear()
        response_clear = self.author_client.get(pages).content
        self.assertNotEqual(response_cache, response_clear)
