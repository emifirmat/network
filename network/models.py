from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """List of registered users"""
    pass

class Post(models.Model):
    """Posts made by users"""
    content = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, 
        related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)

class Follow(models.Model):
    """Relation between users following each other"""
    user_following = models.ForeignKey(User, on_delete=models.CASCADE,
        related_name="following_list")
    user_followed = models.ForeignKey(User, on_delete=models.CASCADE, 
        related_name="followers_list")
    
    def follow_is_valid(self):
        """Following user can't be followed user at the same time"""
        if self.user_following == self.user_followed:
            raise ValidationError(
                "Following and followed can't be the same person")
    
    def __str__(self):
        return f"{self.user_following} is following {self.user_followed}"
    
    class Meta:
        """ Avoid repetetion as each following is unique"""
        unique_together = ("user_following", "user_followed")

class Like(models.Model):
    """Likes made by users on posts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
        related_name="post_likes")
    
    def __str__(self):
        return f"{self.user} liked post n°{self.post.id}."
        
    class Meta:
        """Avoid repetition as each like yo each post is unique"""
        unique_together = ("user", "post")