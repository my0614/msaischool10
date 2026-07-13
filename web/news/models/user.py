from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from news.models.common import BaseModel

class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)
    
    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, password, **extra_fields)
    
class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    username = models.EmailField(max_length=50, unique=True, verbose_name='이메일')
    name = models.CharField(max_length=30, null=True, blank=True, verbose_name='이름')

    # REQUIRED_FIELDS = 'username',
    USERNAME_FIELD = 'username'

    objects = UserManager()

    class Meta:
        verbose_name = '유저'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{} ({})'.format(self.username, self.name)