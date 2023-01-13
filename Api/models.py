from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField('username', max_length=100, unique=True)
    email = models.EmailField('email address', unique=True)
    following = models.ManyToManyField("self", symmetrical=False, blank=True, related_name='followers')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    def __str__(self):
        return self.username


class Idea(models.Model):
    PUBLIC = 'public'
    PROTECTED = 'protected'
    PRIVATE = 'private'
    VISIBILITY_CHOICES = [
        (PUBLIC, 'Public'),
        (PROTECTED, 'Protected'),
        (PRIVATE, 'Private')
    ]
    content = models.CharField(max_length=280, blank=False)
    pub_date = models.DateTimeField(auto_now_add=True)
    pub_user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, related_name='idea_user')
    visibility = models.CharField(max_length=9, choices=VISIBILITY_CHOICES, default=PUBLIC)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.content


class FollowRequest(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DENIED = 'denied'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DENIED, 'Denied')
    ]
    to_follow = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, related_name='follow_recived')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, related_name='follow_send')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f'{self.requester.username} follows {self.to_follow.username}'