from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.conf import settings
from django.core.cache import cache
import requests
import urllib.parse
import re

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default='')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'movies_profile'

    @property
    def unread_notifications_count(self):
        return self.user.notifications.filter(is_read=False).count()

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Movie(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('movie', 'Movie'),
        ('tv_show', 'TV Show'),
        ('web_series', 'Web Series'),
        ('ott', 'OTT Originals'),
        ('documentary', 'Documentary'),
        ('anime', 'Anime'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    poster_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Direct link to a poster image")
    genre = models.CharField(max_length=255, help_text="Comma-separated genres")
    media_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES, default='movie')
    language = models.CharField(max_length=20, choices=(('english', 'English'), ('hindi', 'Hindi')), default='english')
    release_date = models.DateField()
    trailer_url = models.URLField(max_length=1000, blank=True, null=True, help_text="YouTube Embed link")
    cast_info = models.CharField(max_length=500, blank=True, null=True, help_text="Director: X | Stars: Y, Z")

    class Meta:
        db_table = 'movies_movie'

    def __str__(self):
        return self.title

    @property
    def get_poster(self):
        if self.poster_url:
            return self.poster_url
        if self.poster:
            return self.poster.url
        return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"

    @property
    def story_avg(self):
        avg = self.ratings.aggregate(Avg('story_rating'))['story_rating__avg']
        return round(avg, 1) if avg else None

    @property
    def acting_avg(self):
        avg = self.ratings.aggregate(Avg('acting_rating'))['acting_rating__avg']
        return round(avg, 1) if avg else None

    @property
    def music_avg(self):
        avg = self.ratings.aggregate(Avg('music_rating'))['music_rating__avg']
        return round(avg, 1) if avg else None

    @property
    def visual_avg(self):
        avg = self.ratings.aggregate(Avg('visual_rating'))['visual_rating__avg']
        return round(avg, 1) if avg else None

    @property
    def story_percent(self):
        val = self.story_avg
        return int(val * 10) if val else 0

    @property
    def acting_percent(self):
        val = self.acting_avg
        return int(val * 10) if val else 0

    @property
    def music_percent(self):
        val = self.music_avg
        return int(val * 10) if val else 0

    @property
    def visual_percent(self):
        val = self.visual_avg
        return int(val * 10) if val else 0

    @property
    def overall_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return None
        total = 0
        for r in ratings:
            total += (r.story_rating + r.acting_rating + r.music_rating + r.visual_rating) / 4.0
        return round(total / len(ratings), 1)

    @property
    def heat_meter(self):
        val = self.overall_rating
        if not val:
            return "🔥 60% trending"
        percentage = int(val * 10)
        fires = "🔥" * max(1, min(5, int(percentage / 20)))
        return f"{fires} {percentage}% trending"

    @property
    def director(self):
        if not self.cast_info:
            return None
        if "Director:" in self.cast_info:
            parts = self.cast_info.split('|')
            for part in parts:
                if "Director:" in part:
                    return part.replace("Director:", "").strip()
        return None

    @property
    def stars(self):
        if not self.cast_info:
            return None
        if "Stars:" in self.cast_info:
            parts = self.cast_info.split('|')
            for part in parts:
                if "Stars:" in part:
                    return part.replace("Stars:", "").strip()
        if "Director:" not in self.cast_info:
            return self.cast_info.strip()

    @property
    def director_details(self):
        if not self.director:
            return []
        details = []
        for d in self.director.split(','):
            name = d.strip()
            if not name:
                continue
            parts = name.split()
            initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "?"
            
            cache_key = f"person_img_{urllib.parse.quote(name)}"
            img_url = cache.get(cache_key)
            if not img_url:
                api_key = getattr(settings, 'TMDB_API_KEY', '9eeb9108c0facc34d988b94798220a6e')
                base_url = getattr(settings, 'TMDB_API_URL', 'https://api.themoviedb.org/3')
                search_url = f"{base_url}/search/person"
                try:
                    response = requests.get(search_url, params={
                        'api_key': api_key,
                        'query': name,
                        'language': 'en-US'
                    }, timeout=5.0)
                    if response.status_code == 200:
                        results = response.json().get('results', [])
                        if results:
                            profile_path = results[0].get('profile_path')
                            if profile_path:
                                img_url = f"https://image.tmdb.org/t/p/w185{profile_path}"
                                cache.set(cache_key, img_url, 30 * 86400)
                except Exception:
                    pass
            
            details.append({
                'name': name,
                'initials': initials,
                'image_url': img_url or "",
                'google_url': f"https://www.google.com/search?q={name.replace(' ', '+')}"
            })
        return details

    @property
    def stars_details(self):
        if not self.stars:
            return []
        details = []
        for s in self.stars.split(','):
            name = s.strip()
            if not name:
                continue
            parts = name.split()
            initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "?"
            
            cache_key = f"person_img_{urllib.parse.quote(name)}"
            img_url = cache.get(cache_key)
            if not img_url:
                api_key = getattr(settings, 'TMDB_API_KEY', '9eeb9108c0facc34d988b94798220a6e')
                base_url = getattr(settings, 'TMDB_API_URL', 'https://api.themoviedb.org/3')
                search_url = f"{base_url}/search/person"
                try:
                    response = requests.get(search_url, params={
                        'api_key': api_key,
                        'query': name,
                        'language': 'en-US'
                    }, timeout=5.0)
                    if response.status_code == 200:
                        results = response.json().get('results', [])
                        if results:
                            profile_path = results[0].get('profile_path')
                            if profile_path:
                                img_url = f"https://image.tmdb.org/t/p/w185{profile_path}"
                                cache.set(cache_key, img_url, 30 * 86400)
                except Exception:
                    pass
            
            details.append({
                'name': name,
                'initials': initials,
                'image_url': img_url or "",
                'google_url': f"https://www.google.com/search?q={name.replace(' ', '+')}"
            })
        return details

    @property
    def embed_trailer_url(self):
        if not self.trailer_url:
            return ""
        url = self.trailer_url
        if "/embed/" in url:
            return url
        
        reg = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^#\&\?]+)'
        match = re.match(reg, url)
        if match:
            video_id = match.group(4)
            return f"https://www.youtube.com/embed/{video_id}"
        return url

class Rating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    story_rating = models.IntegerField(default=5)
    acting_rating = models.IntegerField(default=5)
    music_rating = models.IntegerField(default=5)
    visual_rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_rating'
        unique_together = ('movie', 'user')

    @property
    def average_score(self):
        return round((self.story_rating + self.acting_rating + self.music_rating + self.visual_rating) / 4.0, 1)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField(default=5, help_text="1 to 10 overall value")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movies_review'

    def __str__(self):
        return f"Review by {self.user.username} on {self.movie.title}"

    @property
    def likes_count(self):
        return self.likes.count()

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_comment'

    def __str__(self):
        return f"Comment by {self.user.username} on Review {self.review.id}"

    @property
    def likes_count(self):
        return self.likes.count()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_like'
        unique_together = ('user', 'review', 'comment')

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_follow'
        unique_together = ('follower', 'following')

class Watchlist(models.Model):
    STATUS_CHOICES = (
        ('watching', 'Watching'),
        ('completed', 'Completed'),
        ('planned', 'Plan to watch'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlist_entries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_watchlist'
        unique_together = ('user', 'movie')

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_notification'

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

class ActivityFeed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_activityfeed'

    def __str__(self):
        return f"{self.user.username} {self.action_text}"

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_bookmark'
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.username} saved review {self.review.id}"

class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_otp')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_emailotp'

    def is_valid(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).total_seconds() < 600

    def __str__(self):
        return f"OTP for {self.user.username}: {self.otp_code}"

class PasswordResetOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_otp')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_passwordresetotp'

    def is_valid(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).total_seconds() < 600

    def __str__(self):
        return f"Reset OTP for {self.user.username}: {self.otp_code}"
