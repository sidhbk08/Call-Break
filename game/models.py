from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=10, default=0, decimal_places=9)
    birth_date = models.DateField(null=True, blank=True)


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class Onuser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ingame = models.BooleanField(default=False)
    online = models.BooleanField(default=True)

class team(models.Model):
	status = models.IntegerField(default=0)
	carddistibutor = models.ForeignKey(Onuser, null=True, on_delete = models.CASCADE, related_name='carddistibutors')
	call_card = models.IntegerField(default=1)
	call_amount = models.IntegerField(default=4)
	call_player = models.ForeignKey(Onuser, on_delete=models.CASCADE, null=True, related_name='call_players')

class cardon(models.Model):
	team = models.ForeignKey(team, on_delete=models.CASCADE)
	cardon = models.IntegerField(null=True)

class player(models.Model):
	team = models.ForeignKey(team, on_delete=models.CASCADE)
	player = models.ForeignKey(Onuser, on_delete = models.CASCADE, null=True)
	score = models.DecimalField(max_digits=3, default=0, decimal_places=1)
	turn = models.IntegerField(default=0)
	state = models.BooleanField(default=False)

class sets(models.Model):
	player = models.ForeignKey(player, on_delete=models.CASCADE)
	final_sc = models.IntegerField(default=2)
	current_sc = models.IntegerField(default=0)

class card(models.Model):
    player = models.ForeignKey(player, on_delete=models.CASCADE)
    card = models.IntegerField()
    active = models.BooleanField(default=False)
