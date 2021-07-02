from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Reader

@receiver(post_save, sender=User)
def create_reader(sender, instance, created, **kwargs):
    if created:
        Reader.objects.create(user=instance)