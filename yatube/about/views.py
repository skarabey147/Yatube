from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """
    Страница "Об авторе"
    """
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """
    Страница "Технологии"
    """
    template_name = 'about/tech.html'
