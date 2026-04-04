from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_student = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    onboarding_complete = models.BooleanField(default=False)
    tutorial_complete = models.BooleanField(default=False)
    
    groups = models.ManyToManyField('auth.Group', verbose_name='groups', blank=True, help_text='The groups this user belongs to.', related_name='custom_user_set', related_query_name='user')
    user_permissions = models.ManyToManyField('auth.Permission', verbose_name='user permissions', blank=True, help_text='Specific permissions for this user.', related_name='custom_user_set', related_query_name='user')

    def __str__(self):
        return self.username