from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def validate_not_empty(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError(
                'А кто поле будет заполнять, Пушкин?',
                params={'data': data},
            )
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)