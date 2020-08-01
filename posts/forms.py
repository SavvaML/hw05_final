from django import forms
from .models import Post, Comment
from django.utils.translation import gettext_lazy as _


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'text': _('Текст записи'),
            'group': _('Сообщества'),
        }
        help_texts = {
            "text": _("Здесь содержание,не ошибись."),
            "group": _("Здесь название,не ошибись."),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        text = forms.CharField(widget=forms.Textarea)
        labels = {
            'text': 'Комментарий'
        }
        help_texts = {
            'text': 'Напишите комментарий тут :)'
        }
