from django.db import models
from django.contrib.auth.models import User, UserManager
import hashlib

EPISODE_ACTION_TYPES = (
        ('download', 'downloaded'),
        ('play',     'played'),
        ('sync',     'synced'),
        ('lock',     'locked'),
        ('delete',   'deleted')
    )

DEVICE_TYPES = (
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('server', 'Server'),
        ('other', 'Other')
    )

SUBSCRIPTION_ACTION_TYPES = (
        ('subscribe', 'subscribed'),
        ('unsubscribe', 'unsubscribed')
    )

#inheriting from User, as described in 
#http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/
class UserAccount(User):
    public_profile = models.BooleanField()

    objects = UserManager()

    def __unicode__(self):
        return self.username
    
    class Meta:
        db_table = 'user'

class Podcast(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()
    last_update = models.DateTimeField()
    logo_url = models.CharField(max_length=1000)
    
    def subscriptions(self):
        return Subscription.objects.filter(podcast=self)
    
    def subscription_count(self):
        return self.subscriptions().count()

    def logo_shortname(self):
        return hashlib.sha1(self.logo_url).hexdigest()

    def __unicode__(self):
        return self.title if self.title != '' else self.url
    
    class Meta:
        db_table = 'podcast'

class Episode(models.Model):
    podcast = models.ForeignKey(Podcast)
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()

    def __unicode__(self):
        return self.title
    
    class Meta:
        db_table = 'episode'

class SyncGroup(models.Model):
    user = models.ForeignKey(User)
    
    def __unicode__(self):
        '%s - %s' % (user, ', '.join(devices = Device.objects.filter(sync_group=self)))
             
    class Meta:
        db_table = 'sync_group'


class Device(models.Model):
    user = models.ForeignKey(User)
    uid = models.SlugField(max_length=50)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    sync_group = models.ForeignKey(SyncGroup, blank=True, null=True)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.type)

    class Meta:
        db_table = 'device'

class EpisodeAction(models.Model):
    user = models.ForeignKey(User, primary_key=True)
    episode = models.ForeignKey(Episode)
    device = models.ForeignKey(Device)
    action = models.CharField(max_length=10, choices=EPISODE_ACTION_TYPES)
    timestamp = models.DateTimeField()
    playmark = models.IntegerField()

    def __unicode__(self):
        return '%s %s %s' % self.user, self.action, self.episode

    class Meta:
        db_table = 'episode_log'


class Subscription(models.Model):
    device = models.ForeignKey(Device, primary_key=True)
    podcast = models.ForeignKey(Podcast)
    user = models.ForeignKey(UserAccount)
    subscribed_since = models.DateTimeField()

    def __unicode__(self):
        return '%s - %s on %s' % (self.device.user, self.podcast, self.device)
    
    class Meta:
        db_table = 'current_subscription'

class SubscriptionAction(models.Model):
    device = models.ForeignKey(Device)
    podcast = models.ForeignKey(Podcast)
    action = models.CharField(max_length=12, choices=SUBSCRIPTION_ACTION_TYPES)
    timestamp = models.DateTimeField()

    def __unicode__(self):
        return '%s %s %s' % (self.device, self.action, self.podcast)
    
    class Meta:
        db_table = 'subscription_log'
        unique_together = ('device', 'podcast', 'action', 'timestamp')

