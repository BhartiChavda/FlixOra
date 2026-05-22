from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Review, Comment, Like, Follow, Watchlist, Notification, ActivityFeed

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# Auto Activity logs & Notifications for Review
@receiver(post_save, sender=Review)
def handle_review_creation(sender, instance, created, **kwargs):
    if created:
        ActivityFeed.objects.create(
            user=instance.user,
            action_text=f"reviewed the movie '{instance.movie.title}' ⭐ {instance.rating}/10"
        )
        # Notify followers about this new review
        followers = Follow.objects.filter(following=instance.user)
        for f in followers:
            Notification.objects.create(
                user=f.follower,
                message=f"{instance.user.username} posted a new review on '{instance.movie.title}'!"
            )

# Auto Activity logs & Notifications for Comment
@receiver(post_save, sender=Comment)
def handle_comment_creation(sender, instance, created, **kwargs):
    if created:
        ActivityFeed.objects.create(
            user=instance.user,
            action_text=f"commented on {instance.review.user.username}'s review of '{instance.review.movie.title}'"
        )
        
        # Notify review author if direct comment
        if not instance.parent:
            if instance.user != instance.review.user:
                Notification.objects.create(
                    user=instance.review.user,
                    message=f"{instance.user.username} commented on your review of '{instance.review.movie.title}'!"
                )
        else: # Notify parent comment author if nested reply
            if instance.user != instance.parent.user:
                Notification.objects.create(
                    user=instance.parent.user,
                    message=f"{instance.user.username} replied to your comment on '{instance.review.movie.title}'!"
                )

# Auto Activity logs & Notifications for Follow
@receiver(post_save, sender=Follow)
def handle_follow_creation(sender, instance, created, **kwargs):
    if created:
        ActivityFeed.objects.create(
            user=instance.follower,
            action_text=f"started following {instance.following.username}"
        )
        Notification.objects.create(
            user=instance.following,
            message=f"{instance.follower.username} started following you!"
        )

# Auto Activity logs & Notifications for Watchlist
@receiver(post_save, sender=Watchlist)
def handle_watchlist_creation(sender, instance, created, **kwargs):
    if created:
        ActivityFeed.objects.create(
            user=instance.user,
            action_text=f"added '{instance.movie.title}' to watchlist as '{instance.get_status_display()}'"
        )
