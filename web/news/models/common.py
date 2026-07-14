import uuid

from django.db import models
from django.utils import timezone


class BaseQuerySet(models.query.QuerySet):
    def delete(self):
        self.update(removed_at=timezone.now())


class ModelManager(models.Manager):
    def get_queryset(self):
        queryset = BaseQuerySet(self.model)
        return queryset.filter(removed_at__isnull=True)


class BaseModel(models.Model):
    objects = ModelManager()

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    removed_at = models.DateTimeField(null=True, blank=True, verbose_name="삭제일")

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.removed_at = timezone.now()
        self.save(update_fields=["removed_at", "updated_at"])

class Sample(BaseModel):
    name = models.CharField(max_length=100, verbose_name="이름")
    phone_number = models.CharField(max_length=20, verbose_name="전화번호")
    address = models.CharField(max_length=200, verbose_name="주소")

    class Meta:
        verbose_name = "샘플"
        verbose_name_plural = "샘플"