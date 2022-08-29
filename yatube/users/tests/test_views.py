from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

User = get_user_model()


class UserViewsTests(TestCase):
    def setUp(self):
        self.user_client = Client()
        self.user = User.objects.create_user(username='test_name')
        self.user_client.force_login(self.user)

    def test_uses_correct_template(self):
        """Проверяем namespase:name и шаблоны."""
        templates_url_names = {
            'users:signup': 'users/signup.html',
            'users:login': 'users/login.html',
            'users:password_change_form': 'users/password_change_form.html',
            'users:password_change_done': 'users/password_change_done.html',
            'users:password_reset_form': 'users/password_reset_form.html',
            'users:password_reset_done': 'users/password_reset_done.html',
            'users:password_reset_confirm': 'users/'
                                            'password_reset_confirm.html',
            'users:password_reset_complete': 'users/'
                                             'password_reset_complete.html',
            'users:logout': 'users/logged_out.html'
        }
        for name, template in templates_url_names.items():
            with self.subTest(name=name):
                token = {}
                if name == 'users:password_reset_confirm':
                    token = {'uidb64': 'empty', 'token': 'empty'}
                response = self.user_client.get(reverse(name, kwargs=token))
                self.assertTemplateUsed(response, template)

    def test_form_signup(self):
        """Проверяем форму users:signup"""
        form = self.user_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField
        }
        for field, answer in form_fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(
                    form.context['form'].fields[field], answer
                )
