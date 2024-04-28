from django import forms

from .models import User, Post

class PostForm(forms.ModelForm):
    """Create a new post"""
    class Meta:
        model = Post
        fields = ["content"]
        labels= {"content": ""}
        widgets = {
            "content": forms.Textarea(attrs={"class": "form-control"}),
        }