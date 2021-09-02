from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        super().setUpClass()
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/."""
        urls = {
            '/about/author/': HTTPStatus.OK.value,
            '/about/tech/': HTTPStatus.OK.value,
        }
        for adress, status_code in urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/."""
        urls = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'
        }
        for template, url in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
