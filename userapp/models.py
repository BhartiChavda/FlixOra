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

        # Use cache to avoid repeated API calls for the same title
        cache_key = f"movie_poster_v4_{urllib.parse.quote(self.title)}"
        cached_poster = cache.get(cache_key)
        if cached_poster:
            return cached_poster

        api_key = getattr(settings, 'TMDB_API_KEY', '9eeb9108c0facc34d988b94798220a6e')
        # We try BOTH urls. 
        # api.themoviedb.org -> works on PythonAnywhere, blocked in India
        # api.tmdb.org -> works in India, blocked on PythonAnywhere
        api_urls = [
            'https://api.themoviedb.org/3',
            'https://api.tmdb.org/3'
        ]
        release_year = self.release_date.year if self.release_date else None
        title_lower = self.title.strip().lower()

        def _find_best_match(results, name_field):
            """Exact title match first, then first result with any poster."""
            for r in results:
                if r.get(name_field, '').strip().lower() == title_lower and r.get('poster_path'):
                    return f"https://image.tmdb.org/t/p/w500{r['poster_path']}"
            for r in results:
                if r.get('poster_path'):
                    return f"https://image.tmdb.org/t/p/w500{r['poster_path']}"
            return None

        def _search_tmdb(endpoint, year_param=None):
            """Search TMDB: first WITH year (accurate), then WITHOUT year (broader)."""
            name_field = 'name' if 'tv' in endpoint else 'title'
            base_params = {'api_key': api_key, 'query': self.title, 'language': 'en-US'}
            
            # Try every URL until one works
            for base_url in api_urls:
                try:
                    # Attempt 1: WITH year filter
                    if year_param and release_year:
                        resp = requests.get(f"{base_url}/{endpoint}",
                            params={**base_params, year_param: release_year}, timeout=5.0)
                        if resp.status_code == 200:
                            match = _find_best_match(resp.json().get('results', []), name_field)
                            if match:
                                return match
                    # Attempt 2: WITHOUT year filter (catches year mismatches)
                    resp = requests.get(f"{base_url}/{endpoint}", params=base_params, timeout=5.0)
                    if resp.status_code == 200:
                        match = _find_best_match(resp.json().get('results', []), name_field)
                        if match:
                            return match
                except Exception:
                    continue # If blocked by ISP or Firewall, just try the next URL!
            return None

        img_url = None

        # Step 1: Search the correct endpoint based on media_type (with year)
        if self.media_type in ['tv_show', 'web_series', 'ott', 'anime']:
            img_url = _search_tmdb('search/tv', 'first_air_date_year')
            # If not found, also try movie endpoint
            if not img_url:
                img_url = _search_tmdb('search/movie', 'year')
        else:
            img_url = _search_tmdb('search/movie', 'year')
            # If not found, also try TV endpoint
            if not img_url:
                img_url = _search_tmdb('search/tv', 'first_air_date_year')

        # Step 2: If TMDB fails, try Google Custom Search API
        if not img_url:
            google_api_key = getattr(settings, 'GOOGLE_API_KEY', None)
            google_cx = getattr(settings, 'GOOGLE_CX', None)
            if google_api_key and google_cx:
                try:
                    query = f"{self.title} {release_year or ''} poster official".strip()
                    resp = requests.get(
                        'https://www.googleapis.com/customsearch/v1',
                        params={
                            'key': google_api_key,
                            'cx': google_cx,
                            'q': query,
                            'searchType': 'image',
                            'num': 1,
                            'imgSize': 'large',
                        },
                        timeout=5.0
                    )
                    if resp.status_code == 200:
                        items = resp.json().get('items', [])
                        if items:
                            img_url = items[0].get('link')
                except Exception:
                    pass

        if img_url:
            cache.set(cache_key, img_url, 30 * 86400)  # Cache for 30 days
            return img_url

        # Final fallback: generic placeholder
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
        # Always use IMDb rating as the overall score, fallback to TMDB
        cache_key = f"movie_imdb_rating_v1_{self.id}"
        cached_rating = cache.get(cache_key)
        if cached_rating is not None:
            return cached_rating if cached_rating != "N/A" else None
            
        imdb_rating = None
        
        # 1. Try to get IMDb rating via open IMDb APIs
        try:
            import urllib.parse
            import re
            query = urllib.parse.quote(self.title)
            # Use IMDb suggestion API to find the IMDb ID
            suggest_url = f"https://v3.sg.media-imdb.com/suggestion/x/{query}.json"
            suggest_resp = requests.get(suggest_url, timeout=3.0)
            if suggest_resp.status_code == 200:
                results = suggest_resp.json().get('d', [])
                if results:
                    # Match by title and year if possible
                    best_match = None
                    release_year = self.release_date.year if self.release_date else None
                    for r in results:
                        if r.get('id', '').startswith('tt') and r.get('l', '').strip().lower() == self.title.strip().lower():
                            if release_year and r.get('y') == release_year:
                                best_match = r
                                break
                            elif not best_match:
                                best_match = r
                    
                    if not best_match:
                        for r in results:
                            if r.get('id', '').startswith('tt'):
                                best_match = r
                                break
                                
                    if best_match:
                        imdb_id = best_match['id']
                        # Fetch the rating from IMDb JSONP endpoint
                        rating_url = f"https://p.media-imdb.com/static-content/documents/v1/title/{imdb_id}/ratings%3Fjsonp=imdb.rating.run:imdb.api.title.ratings/data.json"
                        rating_resp = requests.get(rating_url, timeout=3.0)
                        if rating_resp.status_code == 200:
                            match = re.search(r'"rating":([0-9.]+)', rating_resp.text)
                            if match:
                                imdb_rating = round(float(match.group(1)), 1)
        except Exception:
            pass
            
        # 2. Fallback to TMDB if IMDb fails
        if not imdb_rating:
            api_key = getattr(settings, 'TMDB_API_KEY', '9eeb9108c0facc34d988b94798220a6e')
            api_urls = ['https://api.themoviedb.org/3', 'https://api.tmdb.org/3']
            endpoint = 'search/tv' if self.media_type in ['tv_show', 'web_series', 'ott', 'anime'] else 'search/movie'
            year_param = 'first_air_date_year' if 'tv' in endpoint else 'year'
            release_year = self.release_date.year if self.release_date else None
            
            for base_url in api_urls:
                try:
                    params = {'api_key': api_key, 'query': self.title, 'language': 'en-US'}
                    if release_year:
                        params[year_param] = release_year
                        
                    resp = requests.get(f"{base_url}/{endpoint}", params=params, timeout=3.0)
                    if resp.status_code == 200:
                        results = resp.json().get('results', [])
                        if results:
                            title_lower = self.title.strip().lower()
                            name_field = 'name' if 'tv' in endpoint else 'title'
                            best_match = None
                            for r in results:
                                if r.get(name_field, '').strip().lower() == title_lower:
                                    best_match = r
                                    break
                            if not best_match:
                                best_match = results[0]
                                
                            vote_avg = best_match.get('vote_average')
                            if vote_avg:
                                imdb_rating = round(vote_avg, 1)
                                break
                except Exception:
                    continue
                    
        cache.set(cache_key, imdb_rating if imdb_rating else "N/A", 30 * 86400)
        return imdb_rating

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
        if "Popular globally" in self.cast_info or "Rating:" in self.cast_info:
            return None
        if "Stars:" in self.cast_info:
            parts = self.cast_info.split('|')
            for part in parts:
                if "Stars:" in part:
                    return part.replace("Stars:", "").strip()
        if "Director:" not in self.cast_info:
            return self.cast_info.strip()
        return None

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
            
            cache_key = f"person_img_v2_{urllib.parse.quote(name)}"
            img_url = cache.get(cache_key)
            if not img_url:
                api_key = getattr(settings, 'TMDB_API_KEY', '9eeb9108c0facc34d988b94798220a6e')
                api_urls = ['https://api.themoviedb.org/3', 'https://api.tmdb.org/3']
                for base_url in api_urls:
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
                            break  # Stop trying other URLs if this one succeeds
                    except Exception:
                        continue
            
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
            
            cache_key = f"person_img_v2_{urllib.parse.quote(name)}"
            img_url = cache.get(cache_key)
            if not img_url:
                api_key = getattr(settings, 'TMDB_API_KEY', '9eeb9108c0facc34d988b94798220a6e')
                api_urls = ['https://api.themoviedb.org/3', 'https://api.tmdb.org/3']
                for base_url in api_urls:
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
                            break  # Stop trying other URLs if this one succeeds
                    except Exception:
                        continue
            
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
