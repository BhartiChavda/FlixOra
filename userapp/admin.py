from django.contrib import admin
from .models import Profile, Movie, Rating, Review, Comment, Like, Follow, Watchlist, Notification, ActivityFeed

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'verified')
    list_filter = ('verified',)
    search_fields = ('user__username', 'bio')

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'release_date')
    search_fields = ('title', 'genre', 'description')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'story_rating', 'acting_rating', 'music_rating', 'visual_rating')
    search_fields = ('user__username', 'movie__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'movie__title', 'text')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'parent', 'created_at')
    search_fields = ('user__username', 'text')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'comment', 'created_at')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'status', 'is_public', 'created_at')
    list_filter = ('status', 'is_public')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')

@admin.register(ActivityFeed)
class ActivityFeedAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_text', 'created_at')
