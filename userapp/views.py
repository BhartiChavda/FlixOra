from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Q, Count, Sum
from django.http import JsonResponse
from django.contrib import messages
import datetime
import operator
from functools import reduce
import random
from django.core.mail import send_mail
from django.conf import settings
import requests
from django.utils import timezone
import traceback
import logging

logger = logging.getLogger(__name__)

from .models import Profile, Movie, Rating, Review, Comment, Like, Follow, Watchlist, Notification, ActivityFeed, Bookmark, EmailOTP, PasswordResetOTP
from .forms import ReviewForm, RatingForm, CommentForm, ProfileForm, WatchlistForm, UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

# Mood to Genre Mapping
MOOD_GENRE_MAP = {
    'happy': ['Comedy', 'Romance', 'Family', 'Musical', 'Animation'],
    'sad': ['Drama', 'Family', 'Biography', 'Documentary'],
    'excited': ['Action', 'Science Fiction', 'Adventure', 'Thriller', 'Horror', 'Mystery'],
    'bored': ['Mystery', 'Crime', 'Fantasy', 'Adventure', 'Science Fiction']
}

# TMDB TV/Movie Genre Map
TMDB_GENRES_MAP = {
    # Movie Genres
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    # TV Genres
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality",
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics"
}

def map_tmdb_genres(genre_ids):
    names = [TMDB_GENRES_MAP.get(gid) for gid in genre_ids if TMDB_GENRES_MAP.get(gid)]
    return ", ".join(names) if names else "Drama"

# High quality fallbacks when TMDB times out or network is down
FALLBACK_DATA = {
    'tv_show': [
        {
            'title': 'Breaking Bad',
            'description': 'A high school chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine with a former student.',
            'genre': 'Drama, Crime',
            'release_date': '2008-01-20',
            'poster_url': 'https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creator: Vince Gilligan | Stars: Bryan Cranston, Aaron Paul',
            'language': 'english'
        },
        {
            'title': 'Game of Thrones',
            'description': 'Nine noble families fight for control over the lands of Westeros, while an ancient enemy returns after being dormant for thousands of years.',
            'genre': 'Action, Adventure, Fantasy',
            'release_date': '2011-04-17',
            'poster_url': 'https://images.unsplash.com/photo-1568832359672-e36cf5d74f54?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creators: David Benioff, D.B. Weiss | Stars: Emilia Clarke, Kit Harington',
            'language': 'english'
        },
        {
            'title': 'Stranger Things',
            'description': 'When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.',
            'genre': 'Drama, Fantasy, Horror',
            'release_date': '2016-07-15',
            'poster_url': 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creators: Duffer Brothers | Stars: Millie Bobby Brown, Winona Ryder',
            'language': 'english'
        },
        {
            'title': 'Panchayat',
            'description': 'A comedy-drama, which captures the journey of an engineering graduate Abhishek, who joins as a secretary of a Panchayat office in a remote village of Uttar Pradesh.',
            'genre': 'Comedy, Drama',
            'release_date': '2020-04-03',
            'poster_url': 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Director: Deepak Kumar Mishra | Stars: Jitendra Kumar, Raghubir Yadav',
            'language': 'hindi'
        },
        {
            'title': 'Delhi Crime',
            'description': 'Based on the case files of the Delhi Police, this series follows the investigation into the horrific gang rape of a young woman.',
            'genre': 'Drama, Crime, Anthology',
            'release_date': '2019-03-22',
            'poster_url': 'https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Director: Richie Mehta | Stars: Shefali Shah, Rajesh Tailang',
            'language': 'hindi'
        }
    ],
    'web_series': [
        {
            'title': 'The Boys',
            'description': 'A fun and irreverent take on what happens when superheroes—who are as popular as celebrities—abuse their superpowers.',
            'genre': 'Sci-Fi, Action, Drama',
            'release_date': '2019-07-26',
            'poster_url': 'https://images.unsplash.com/photo-1569003339405-ea396a5a8a90?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creator: Eric Kripke | Stars: Karl Urban, Jack Quaid',
            'language': 'english'
        },
        {
            'title': 'Sacred Games',
            'description': 'A link in their pasts leads an honest cop to a fugitive gang boss, whose cryptic warning spurs the officer on a quest to save Mumbai from cataclysm.',
            'genre': 'Action, Crime, Drama',
            'release_date': '2018-07-06',
            'poster_url': 'https://images.unsplash.com/photo-1601513525393-8393e5993b37?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Directors: Anurag Kashyap, Vikramaditya Motwane | Stars: Saif Ali Khan, Nawazuddin Siddiqui',
            'language': 'hindi'
        },
        {
            'title': 'Mirzapur',
            'description': 'A shocking incident at a wedding procession ignites a series of events, entangling the lives of two families in the lawless city of Mirzapur.',
            'genre': 'Action, Crime, Drama',
            'release_date': '2018-11-16',
            'poster_url': 'https://images.unsplash.com/photo-1585647347483-22b66260dfff?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creators: Karan Anshuman, Puneet Krishna | Stars: Pankaj Tripathi, Ali Fazal',
            'language': 'hindi'
        }
    ],
    'ott': [
        {
            'title': 'Squid Game',
            'description': 'Hundreds of cash-strapped players accept a strange invitation to compete in children\'s games. Inside, a tempting prize awaits with deadly high stakes.',
            'genre': 'Action, Thriller, Drama',
            'release_date': '2021-09-17',
            'poster_url': 'https://images.unsplash.com/photo-1627856013091-fed6e4e30025?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creator: Hwang Dong-hyuk | Stars: Lee Jung-jae, Park Hae-soo',
            'language': 'english'
        },
        {
            'title': 'The Family Man',
            'description': 'A middle-class man secretly working as an intelligence officer for the T.A.S.C, a fictitious branch of the National Investigation Agency.',
            'genre': 'Action, Comedy, Drama',
            'release_date': '2019-09-20',
            'poster_url': 'https://images.unsplash.com/photo-1509281373149-e957c6296406?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creators: Raj & DK | Stars: Manoj Bajpayee, Sharib Hashmi',
            'language': 'hindi'
        },
        {
            'title': 'Ted Lasso',
            'description': 'American college football coach Ted Lasso heads to London to manage a struggling English Premier League football team.',
            'genre': 'Comedy, Drama, Sports',
            'release_date': '2020-08-14',
            'poster_url': 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Creators: Bill Lawrence, Jason Sudeikis | Stars: Jason Sudeikis, Hannah Waddingham',
            'language': 'english'
        }
    ],
    'documentary': [
        {
            'title': 'Our Planet',
            'description': 'Experiencing our planet\'s natural beauty and examining how climate change impacts all living creatures in this ambitious documentary.',
            'genre': 'Documentary, Nature',
            'release_date': '2019-04-05',
            'poster_url': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Narrator: David Attenborough',
            'language': 'english'
        },
        {
            'title': 'House of Secrets: The Burari Deaths',
            'description': 'Suicide, murder or something else? This docuseries examines chilling truths and theories around the deaths of 11 members of a Delhi family.',
            'genre': 'Documentary, Crime, Mystery',
            'release_date': '2021-10-08',
            'poster_url': 'https://images.unsplash.com/photo-1509248961158-e54f6934749c?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Director: Leena Yadav',
            'language': 'hindi'
        },
        {
            'title': 'The Last Dance',
            'description': 'Charting the rise of the 1990s Chicago Bulls, led by Michael Jordan, featuring never-before-seen footage from the iconic 1997-98 season.',
            'genre': 'Documentary, Biography, Sports',
            'release_date': '2020-04-19',
            'poster_url': 'https://images.unsplash.com/photo-1546519638-68e109498ffc?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Director: Jason Hehir | Stars: Michael Jordan, Scottie Pippen',
            'language': 'english'
        }
    ],
    'anime': [
        {
            'title': 'Attack on Titan',
            'description': 'After his hometown is destroyed and his mother is killed, young Eren Jaeger vows to cleanse the earth of the giant humanoid Titans that have brought humanity to the brink of extinction.',
            'genre': 'Animation, Action, Adventure, Fantasy',
            'release_date': '2013-04-07',
            'poster_url': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Stars: Yuki Kaji, Yui Ishikawa, Marina Inoue',
            'language': 'english'
        },
        {
            'title': 'Demon Slayer: Kimetsu no Yaiba',
            'description': 'A family is attacked by demons and only two members survive - Tanjiro and his sister Nezuko, who is turning into a demon slowly. Tanjiro sets out to become a demon slayer to avenge his family and cure his sister.',
            'genre': 'Animation, Action, Fantasy',
            'release_date': '2019-04-06',
            'poster_url': 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Stars: Natsuki Hanae, Akari Kito, Yoshitsugu Matsuoka',
            'language': 'hindi'
        },
        {
            'title': 'Death Note',
            'description': 'An intelligent high school student goes on a secret crusade to eliminate criminals from the world after discovering a notebook capable of killing anyone whose name is written in it.',
            'genre': 'Animation, Crime, Drama, Mystery',
            'release_date': '2006-10-04',
            'poster_url': 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=500&auto=format&fit=crop',
            'cast_info': 'Stars: Mamoru Miyano, Brad Swaile, Vincent Tong',
            'language': 'english'
        }
    ]
}

def fetch_and_import_tmdb_content(media_type):
    """
    Calls the TMDB API to fetch popular movies or TV shows and auto-imports them to SQLite.
    If the API request fails or times out, it uses a high-quality fallback dataset.
    """
    # Performance Optimization: If content of this media type already exists, skip fetching
    if Movie.objects.filter(media_type=media_type).exists():
        return 0

    api_key = getattr(settings, 'TMDB_API_KEY', None)
    base_url = getattr(settings, 'TMDB_API_URL', 'https://api.themoviedb.org/3')
    image_base = getattr(settings, 'TMDB_IMAGE_BASE', 'https://image.tmdb.org/t/p/w500')
    
    # TV Show / Web Series / OTT / Documentary all map to TMDB TV endpoint (except movie)
    # If media_type is documentary, we also query with genre filter or query
    endpoint_type = "movie" if media_type == "movie" else "tv"
    url = f"{base_url}/{endpoint_type}/popular"
    
    # Custom params for documentaries to query TMDB documentaries
    params = {
        "api_key": api_key,
        "language": "en-US",
        "page": 1
    }
    
    if media_type == "documentary":
        # Genre ID 99 is Documentary in TMDB
        url = f"{base_url}/discover/{endpoint_type}"
        params["with_genres"] = "99"
    elif media_type == "anime":
        # Genre ID 16 is Animation, and original language Japan (ja)
        url = f"{base_url}/discover/{endpoint_type}"
        params["with_genres"] = "16"
        params["with_original_language"] = "ja"
    
    raw_results = []
    if api_key:
        try:
            resp = requests.get(url, params=params, timeout=2.0)
            if resp.status_code == 200:
                raw_results = resp.json().get('results', [])[:10]
        except Exception as e:
            print(f"TMDB connection failed/timeout for {media_type}: {e}")
        
    imported_count = 0
    if raw_results:
        for item in raw_results:
            title = item.get('title') if endpoint_type == "movie" else item.get('name')
            if not title:
                continue
            
            # Check if title already exists in the database
            if Movie.objects.filter(title=title).exists():
                continue
            
            genre_ids = item.get('genre_ids', [])
            genre_str = map_tmdb_genres(genre_ids)
            
            poster_path = item.get('poster_path')
            poster_url = f"{image_base}{poster_path}" if poster_path else "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
            
            date_str = item.get('release_date') if endpoint_type == "movie" else item.get('first_air_date')
            if date_str:
                try:
                    release_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    release_date = datetime.date.today()
            else:
                release_date = datetime.date.today()
                
            orig_lang = item.get('original_language', 'en')
            lang = 'hindi' if orig_lang == 'hi' else 'english'
            
            Movie.objects.create(
                title=title,
                genre=genre_str,
                release_date=release_date,
                description=item.get('overview') or "No description available.",
                poster_url=poster_url,
                cast_info=f"Popular globally on TMDB | Rating: {item.get('vote_average', 0.0)}/10",
                media_type=media_type,
                language=lang
            )
            imported_count += 1
    else:
        # Fallback dataset
        fallback_list = FALLBACK_DATA.get(media_type, [])
        for item in fallback_list:
            if Movie.objects.filter(title=item['title']).exists():
                continue
            
            try:
                release_date = datetime.datetime.strptime(item['release_date'], '%Y-%m-%d').date()
            except Exception:
                release_date = datetime.date.today()
                
            Movie.objects.create(
                title=item['title'],
                genre=item['genre'],
                release_date=release_date,
                description=item['description'],
                poster_url=item['poster_url'],
                cast_info=item['cast_info'],
                media_type=media_type,
                language=item.get('language', 'english')
            )
            imported_count += 1
            
    return imported_count


def calculate_trending_movies():
    movies = Movie.objects.all()
    movie_scores = []
    seven_days_ago = timezone.now() - datetime.timedelta(days=7)
    
    for m in movies:
        rating_score = (m.overall_rating or 5.0) * 10
        reviews = m.reviews.all()
        review_count = reviews.count()
        
        # Likes on reviews
        total_likes = Like.objects.filter(review__movie=m).count()
        
        # Recent activity boost
        recent_count = reviews.filter(created_at__gte=seven_days_ago).count()
        boost = recent_count * 15
        
        score = rating_score + (review_count * 5) + (total_likes * 3) + boost
        movie_scores.append((m, score))
        
    movie_scores.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in movie_scores[:10]]

def get_ai_recommendations(user):
    user_ratings = Rating.objects.filter(user=user)
    liked_genres = set()
    for ur in user_ratings:
        if ur.average_score >= 7.0:
            for g in ur.movie.genre.split(','):
                liked_genres.add(g.strip())
                
    watchlist_entries = Watchlist.objects.filter(user=user)
    for wl in watchlist_entries:
        for g in wl.movie.genre.split(','):
            liked_genres.add(g.strip())
            
    if not liked_genres:
        liked_genres = {'Action', 'Sci-Fi', 'Adventure', 'Comedy', 'Drama'}
        
    rated_ids = [ur.movie.id for ur in user_ratings]
    watchlist_ids = [wl.movie.id for wl in watchlist_entries]
    exclude_ids = set(rated_ids + watchlist_ids)
    
    recommendations = []
    all_movies = Movie.objects.all()
    for m in all_movies:
        if m.id in exclude_ids:
            continue
        match_count = sum(1 for g in m.genre.split(',') if g.strip() in liked_genres)
        if match_count > 0:
            recommendations.append((m, match_count))
            
    recommendations.sort(key=lambda x: (x[1], x[0].overall_rating or 0), reverse=True)
    return [r[0] for r in recommendations[:6]]

def register_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False  # Deactivate user until OTP verified
            user.save()
            
            # Generate OTP
            otp_val = str(random.randint(100000, 999999))
            EmailOTP.objects.update_or_create(user=user, defaults={'otp_code': otp_val})
            
            # Send Email
            subject = "FlixOra OTP Verification Code"
            body = f"Welcome to FlixOra, {user.username}!\n\nYour 6-digit verification code is: {otp_val}\nThis code is valid for 10 minutes."
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.info(request, "A 6-digit verification code has been sent to your email address.")
            except Exception as e:
                messages.warning(request, "Registration succeeded but there was an error sending the verification email. Check console logs.")
                print(f"Error sending email: {e}")
                
            request.session['otp_user_id'] = user.id
            return redirect('verify_otp')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form})

def verify_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, "Session expired or invalid registration attempt. Please sign up again.")
        return redirect('register')
        
    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        login(request, user)
        return redirect('dashboard')
        
    if request.method == 'POST':
        otp_entered = request.POST.get('otp_code', '').strip()
        try:
            otp_record = user.email_otp
            if otp_record.otp_code == otp_entered:
                if otp_record.is_valid():
                    # Activate user
                    user.is_active = True
                    user.save()
                    otp_record.delete()
                    
                    # Log user in
                    login(request, user)
                    del request.session['otp_user_id']
                    
                    messages.success(request, f"Welcome to FlixOra, {user.username}! Your critic account is active.")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Your verification code has expired. Please request a new code.")
            else:
                messages.error(request, "Invalid verification code. Please try again.")
        except EmailOTP.DoesNotExist:
            messages.error(request, "Verification code not found. Please request a new code.")
            
    return render(request, 'user/verify_otp.html', {'email': user.email})

def resend_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, "Session expired or invalid registration attempt.")
        return redirect('register')
        
    user = get_object_or_404(User, id=user_id)
    otp_val = str(random.randint(100000, 999999))
    EmailOTP.objects.update_or_create(user=user, defaults={'otp_code': otp_val, 'created_at': timezone.now()})
    
    # Send Email
    subject = "FlixOra New OTP Verification Code"
    body = f"Hello {user.username},\n\nYour new verification code is: {otp_val}\nThis code is valid for 10 minutes."
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, "A new verification code has been sent to your email address.")
    except Exception as e:
        messages.warning(request, "Error sending verification code. Check console logs.")
        print(f"Error sending email: {e}")
        
    return redirect('verify_otp')

def login_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'user/login.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')

def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'user/forgot_password.html')
            
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.filter(username=email).first()
            
        if user:
            otp_val = str(random.randint(100000, 999999))
            PasswordResetOTP.objects.update_or_create(user=user, defaults={'otp_code': otp_val, 'created_at': timezone.now()})
            
            subject = "FlixOra Password Reset OTP"
            body = f"Hello {user.username},\n\nYour password reset verification code is: {otp_val}\nThis code is valid for 10 minutes."
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.info(request, f"A password reset OTP has been sent to your email ({user.email}).")
            except Exception as e:
                messages.warning(request, f"[TEST MODE] OTP: {otp_val} (Email sending failed: {e})")
                print(f"Password reset OTP error: {e}")
                
            request.session['reset_user_id'] = user.id
            return redirect('reset_password')
        else:
            messages.error(request, "No critic account found with that email/username.")
            
    return render(request, 'user/forgot_password.html')

def reset_password(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, "Invalid password reset session. Please request a code first.")
        return redirect('forgot_password')
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp_code', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            messages.error(request, "Please fill in all password fields.")
            return render(request, 'user/reset_password.html', {'email': user.email})
            
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'user/reset_password.html', {'email': user.email})
            
        try:
            otp_record = user.password_reset_otp
            if otp_record.otp_code == otp_entered:
                if otp_record.is_valid():
                    user.set_password(new_password)
                    user.is_active = True
                    user.save()
                    otp_record.delete()
                    
                    if 'reset_user_id' in request.session:
                        del request.session['reset_user_id']
                    
                    messages.success(request, "Password reset successfully! You can now login.")
                    return redirect('login')
                else:
                    messages.error(request, "Your reset code has expired. Please request a new code.")
            else:
                messages.error(request, "Invalid reset code. Please try again.")
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, "No active reset code found. Please request one.")
            return redirect('forgot_password')
            
    return render(request, 'user/reset_password.html', {'email': user.email})

@login_required
def dashboard(request):
    movies = Movie.objects.all().order_by('-release_date')
    trending_movies = calculate_trending_movies()
    ai_recommendations = get_ai_recommendations(request.user)
    
    # Calculate unread notifications count
    unread_notifs = Notification.objects.filter(user=request.user, is_read=False).count()

    featured_movie = random.choice(list(movies)) if movies.exists() else None

    return render(request, 'user/dashboard.html', {
        'movies': movies,
        'featured_movie': featured_movie,
        'trending_movies': trending_movies,
        'ai_recommendations': ai_recommendations,
        'unread_notifs': unread_notifs,
    })

@login_required
def mood_recommendation(request):
    try:
        media_type = request.GET.get('media_type', '').lower()
        language = request.GET.get('language', '').lower()
        mood = request.GET.get('mood', '').lower()
        search_query = request.GET.get('q', '').strip()
        
        if media_type:
            if media_type in ['movie', 'tv_show', 'web_series', 'ott', 'documentary', 'anime']:
                fetch_and_import_tmdb_content(media_type)
            movies = Movie.objects.filter(media_type=media_type)
        elif mood:
            genres = MOOD_GENRE_MAP.get(mood, [])
            if genres:
                query = reduce(operator.or_, (Q(genre__icontains=g) for g in genres))
                movies = Movie.objects.filter(query)
            else:
                movies = Movie.objects.all()
        else:
            movies = Movie.objects.all()

        if language in ['english', 'hindi']:
            movies = movies.filter(language=language)

        if search_query:
            movies = movies.filter(
                Q(title__icontains=search_query) | 
                Q(genre__icontains=search_query) | 
                Q(description__icontains=search_query)
            )

        movies = sorted(movies, key=lambda m: m.overall_rating or 0, reverse=True)

        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
            request.GET.get('ajax') == 'true' or
            request.META.get('CONTENT_TYPE') == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')
        )
        if is_ajax:
            movies_list = []
            for movie in movies:
                movies_list.append({
                    'id': movie.id,
                    'title': movie.title,
                    'description': movie.description,
                    'genre': movie.genre,
                    'release_date': movie.release_date.strftime('%Y'),
                    'avg_rating': movie.overall_rating if movie.overall_rating else "N/A",
                    'heat_meter': movie.heat_meter,
                    'poster_url': movie.get_poster,
                    'cast_info': movie.cast_info or "Cast info coming soon...",
                    'media_type_display': movie.get_media_type_display(),
                })
            return JsonResponse({'movies': movies_list, 'media_type': media_type, 'mood': mood})

        return redirect('dashboard')
    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR IN mood_recommendation VIEW:")
        print(tb)
        logger.error(f"Error in mood_recommendation: {e}", exc_info=True)
        return JsonResponse({'error': str(e), 'traceback': tb, 'movies': []}, status=500)

@login_required
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    reviews = movie.reviews.select_related('user', 'user__profile').prefetch_related('comments', 'comments__replies').order_by('-created_at')
    
    user_rating = Rating.objects.filter(movie=movie, user=request.user).first()
    user_review = Review.objects.filter(movie=movie, user=request.user).first()
    watchlist_entry = Watchlist.objects.filter(user=request.user, movie=movie).first()

    watch_suggestion = "WATCH" if (movie.overall_rating and movie.overall_rating >= 7.0) or not movie.overall_rating else "SKIP"

    # Forms
    rating_form = RatingForm(instance=user_rating)
    review_form = ReviewForm(instance=user_review)
    watchlist_form = WatchlistForm(instance=watchlist_entry)
    comment_form = CommentForm()

    if request.method == 'POST':
        # Submit category scores
        if 'submit_rating' in request.POST:
            rating_form = RatingForm(request.POST, instance=user_rating)
            if rating_form.is_valid():
                r = rating_form.save(commit=False)
                r.movie = movie
                r.user = request.user
                r.save()
                messages.success(request, "Category scores saved!")
                return redirect('movie_detail', pk=pk)
        
        # Submit or edit written review
        elif 'submit_review' in request.POST:
            review_form = ReviewForm(request.POST, instance=user_review)
            if review_form.is_valid():
                rev = review_form.save(commit=False)
                rev.movie = movie
                rev.user = request.user
                rev.save()
                messages.success(request, "Your movie review bubble is live!")
                return redirect('movie_detail', pk=pk)
                
        # Watchlist toggle
        elif 'submit_watchlist' in request.POST:
            watchlist_form = WatchlistForm(request.POST, instance=watchlist_entry)
            if watchlist_form.is_valid():
                wl = watchlist_form.save(commit=False)
                wl.user = request.user
                wl.movie = movie
                wl.save()
                messages.success(request, f"Watchlist status updated to: {wl.get_status_display()}!")
                return redirect('movie_detail', pk=pk)

    # Calculate related movies based on matching genres
    genres_list = [g.strip() for g in movie.genre.split(',') if g.strip()]
    related_movies = Movie.objects.none()
    if genres_list:
        genre_query = reduce(operator.or_, (Q(genre__icontains=g) for g in genres_list))
        related_movies = Movie.objects.filter(genre_query).exclude(id=movie.id).distinct().order_by('-release_date')[:6]

    return render(request, 'user/movie_detail.html', {
        'movie': movie,
        'reviews': reviews,
        'rating_form': rating_form,
        'review_form': review_form,
        'watchlist_form': watchlist_form,
        'comment_form': comment_form,
        'user_rating': user_rating,
        'user_review': user_review,
        'watchlist_entry': watchlist_entry,
        'watch_suggestion': watch_suggestion,
        'related_movies': related_movies,
    })


# Add review comment views (AJAX supported)
@login_required
def add_comment(request, review_id):
    from django.urls import reverse
    if request.method == 'POST':
        review = get_object_or_404(Review, pk=review_id)
        parent_id = request.POST.get('parent_id')
        parent_comment = None
        if parent_id:
            parent_comment = get_object_or_404(Comment, pk=parent_id)
            
        text = request.POST.get('text', '').strip()
        if text:
            comment = Comment.objects.create(
                user=request.user,
                review=review,
                parent=parent_comment,
                text=text
            )
            
            # Send Notification for comments / replies
            if parent_comment:
                if parent_comment.user != request.user:
                    Notification.objects.create(
                        user=parent_comment.user,
                        message=f"{request.user.username} replied to your comment on '{review.movie.title}'!"
                    )
            else:
                if review.user != request.user:
                    Notification.objects.create(
                        user=review.user,
                        message=f"{request.user.username} commented on your review bubble for '{review.movie.title}'!"
                    )
                    
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                user_verified = False
                if hasattr(request.user, 'profile'):
                    user_verified = request.user.profile.verified
                return JsonResponse({
                    'id': comment.id,
                    'user': comment.user.username,
                    'user_verified': user_verified,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p')
                })
            messages.success(request, "Reply published!")
        else:
            messages.error(request, "Cannot post empty reply.")
            
    return redirect(reverse('movie_detail', kwargs={'pk': review.movie.id}) + f'#review-{review.id}')

@login_required
def toggle_like(request):
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        comment_id = request.POST.get('comment_id')
        
        review = get_object_or_404(Review, pk=review_id) if review_id else None
        comment = get_object_or_404(Comment, pk=comment_id) if comment_id else None
        
        # Prevent duplicate likes
        like_filter = Q(user=request.user)
        if review:
            like_filter &= Q(review=review)
        if comment:
            like_filter &= Q(comment=comment)
            
        like = Like.objects.filter(like_filter).first()
        
        liked = False
        if like:
            like.delete()
        else:
            Like.objects.create(user=request.user, review=review, comment=comment)
            liked = True
            
            # Send Notification for review likes
            if review and review.user != request.user:
                Notification.objects.create(
                    user=review.user,
                    message=f"{request.user.username} liked your review on '{review.movie.title}'!"
                )
            # Send Notification for comment likes
            elif comment and comment.user != request.user:
                Notification.objects.create(
                    user=comment.user,
                    message=f"{request.user.username} liked your comment on '{comment.review.movie.title}'!"
                )
                
        # Total counts
        total_likes = Like.objects.filter(review=review).count() if review else Like.objects.filter(comment=comment).count()
        
        return JsonResponse({
            'liked': liked,
            'total_likes': total_likes,
            'count': total_likes
        })
    return JsonResponse({'error': 'POST required'}, status=400)

@login_required
def toggle_bookmark(request):
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        bookmark = Bookmark.objects.filter(user=request.user, review=review).first()
        saved = False
        if bookmark:
            bookmark.delete()
        else:
            Bookmark.objects.create(user=request.user, review=review)
            saved = True
        return JsonResponse({
            'saved': saved
        })
    return JsonResponse({'error': 'POST required'}, status=400)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    movie_id = review.movie.id
    review.delete()
    messages.info(request, "Review deleted.")
    return redirect('movie_detail', pk=movie_id)

@login_required
def toggle_follow(request, username):
    if request.method == 'POST':
        target_user = get_object_or_404(User, username=username)
        if target_user != request.user:
            follow = Follow.objects.filter(follower=request.user, following=target_user).first()
            if follow:
                follow.delete()
                followed = False
            else:
                Follow.objects.create(follower=request.user, following=target_user)
                followed = True
                
                # Send Follow Notification
                Notification.objects.create(
                    user=target_user,
                    message=f"{request.user.username} started following you!"
                )
                
            return JsonResponse({
                'followed': followed,
                'follower_count': target_user.followers.count(),
                'following_count': target_user.following.count()
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def user_connections_json(request, username):
    target_user = get_object_or_404(User, username=username)
    conn_type = request.GET.get('type', 'following')
    
    my_following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    
    data = []
    if conn_type == 'followers':
        connections = Follow.objects.filter(following=target_user).select_related('follower', 'follower__profile')
        for conn in connections:
            user = conn.follower
            avatar_char = user.username[0].upper() if user.username else '?'
            bio = user.profile.bio if hasattr(user, 'profile') and user.profile.bio else ''
            verified = user.profile.verified if hasattr(user, 'profile') else False
            data.append({
                'username': user.username,
                'avatar_char': avatar_char,
                'bio': bio,
                'verified': verified,
                'is_following': user.id in my_following_ids,
                'is_self': user.id == request.user.id
            })
    else:  # following
        connections = Follow.objects.filter(follower=target_user).select_related('following', 'following__profile')
        for conn in connections:
            user = conn.following
            avatar_char = user.username[0].upper() if user.username else '?'
            bio = user.profile.bio if hasattr(user, 'profile') and user.profile.bio else ''
            verified = user.profile.verified if hasattr(user, 'profile') else False
            data.append({
                'username': user.username,
                'avatar_char': avatar_char,
                'bio': bio,
                'verified': verified,
                'is_following': user.id in my_following_ids,
                'is_self': user.id == request.user.id
            })
            
    return JsonResponse({'connections': data})

@login_required
def following_feed(request):
    # Retrieve critics followed by current user
    following_users = User.objects.filter(followers__follower=request.user)
    reviews = Review.objects.filter(user__in=following_users).select_related('user', 'movie', 'user__profile').order_by('-created_at')
    
    # Stats for current user
    user_reviews_count = Review.objects.filter(user=request.user).count()
    user_following_count = Follow.objects.filter(follower=request.user).count()
    user_followers_count = Follow.objects.filter(following=request.user).count()
    
    # Recommendations (exclude self and already followed users)
    already_following = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    who_to_follow = User.objects.exclude(id=request.user.id).exclude(id__in=already_following).select_related('profile')[:5]
    
    return render(request, 'user/following_feed.html', {
        'reviews': reviews,
        'user_reviews_count': user_reviews_count,
        'user_following_count': user_following_count,
        'user_followers_count': user_followers_count,
        'who_to_follow': who_to_follow,
    })

@login_required
def global_activity_feed(request):
    activities = ActivityFeed.objects.filter(user=request.user).select_related('user', 'user__profile').order_by('-created_at')[:40]
    
    # Stats for current user
    user_reviews_count = Review.objects.filter(user=request.user).count()
    user_following_count = Follow.objects.filter(follower=request.user).count()
    user_followers_count = Follow.objects.filter(following=request.user).count()
    
    # Recommendations (exclude self and already followed users)
    already_following = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    who_to_follow = User.objects.exclude(id=request.user.id).exclude(id__in=already_following).select_related('profile')[:5]
    
    return render(request, 'user/activity_feed.html', {
        'activities': activities,
        'user_reviews_count': user_reviews_count,
        'user_following_count': user_following_count,
        'user_followers_count': user_followers_count,
        'who_to_follow': who_to_follow,
    })

@login_required
def notifications_view(request):
    notifications_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications_list = list(notifications_qs)
    notifications_qs.filter(is_read=False).update(is_read=True)
    return render(request, 'user/notifications.html', {
        'notifications': notifications_list
    })

@login_required
def search_filter(request):
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '').strip()
    rating = request.GET.get('rating', '').strip()
    media_type = request.GET.get('media_type', '').strip()
    year = request.GET.get('year', '').strip()
    
    all_movies = Movie.objects.all().order_by('-release_date')
    movies = all_movies
    users = User.objects.filter(is_active=True)
    reviews = Review.objects.all()
    
    is_filtered = bool(query or genre or rating or media_type or year)
    
    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(genre__icontains=query))
        users = users.filter(Q(username__icontains=query) | Q(profile__bio__icontains=query))
        reviews = reviews.filter(Q(text__icontains=query))
        
    if genre:
        movies = movies.filter(genre__icontains=genre)
    if year:
        movies = movies.filter(release_date__year=year)
        
    if media_type:
        movies = movies.filter(media_type=media_type)
            
    if rating:
        try:
            rating_val = float(rating)
            movies = [m for m in movies if m.overall_rating and m.overall_rating >= rating_val]
        except ValueError:
            pass
            
    if query:
        query_lower = query.lower()
        movies_list = list(movies)
        
        def get_relevance_score(movie):
            t = movie.title.lower()
            d = movie.description.lower() if movie.description else ''
            g = movie.genre.lower() if movie.genre else ''
            if t == query_lower:
                return 4
            elif t.startswith(query_lower):
                return 3
            elif query_lower in t:
                return 2
            elif query_lower in g:
                return 1
            else:
                return 0
                
        movies = sorted(movies_list, key=get_relevance_score, reverse=True)
            
    if not query and (genre or rating or media_type or year):
        if isinstance(movies, list):
            movie_ids = [m.id for m in movies]
            reviews = reviews.filter(movie_id__in=movie_ids)
        else:
            reviews = reviews.filter(movie__in=movies)
        users = users.filter(id__in=reviews.values_list('user_id', flat=True).distinct())
            
    return render(request, 'user/search_results.html', {
        'movies': movies,
        'all_movies': all_movies,
        'is_filtered': is_filtered,
        'users': users,
        'reviews': reviews,
        'query': query,
        'genre': genre,
        'rating': rating,
        'media_type': media_type,
        'year': year,
    })

@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    ratings = Rating.objects.filter(user=profile_user).select_related('movie')
    reviews = Review.objects.filter(user=profile_user).select_related('movie')
    
    total_likes_received = Like.objects.filter(Q(review__user=profile_user) | Q(comment__user=profile_user)).count()
    
    watchlists = Watchlist.objects.filter(user=profile_user)
    if profile_user != request.user:
        watchlists = watchlists.filter(is_public=True)
        
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    
    profile_form = ProfileForm(instance=profile_user.profile)
    password_form = PasswordChangeForm(user=request.user)
    
    if request.method == 'POST' and request.user == profile_user:
        form_type = request.POST.get('form_type')
        if form_type == 'profile':
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile_user.profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Critic Profile updated successfully!")
                return redirect('user_profile', username=username)
        elif form_type == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password was successfully updated!")
                return redirect('user_profile', username=username)
            else:
                messages.error(request, "Error changing password. Please correct the fields below.")

    followers = Follow.objects.filter(following=profile_user).select_related('follower', 'follower__profile')
    following = Follow.objects.filter(follower=profile_user).select_related('following', 'following__profile')
    my_following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))

    return render(request, 'user/profile.html', {
        'profile_user': profile_user,
        'ratings': ratings,
        'reviews': reviews,
        'total_likes': total_likes_received,
        'watchlists': watchlists,
        'is_following': is_following,
        'profile_form': profile_form,
        'password_form': password_form,
        'followers_list': followers,
        'following_list': following,
        'my_following_ids': my_following_ids,
    })

import time

@login_required
def request_email_change(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            new_email = data.get('new_email', '').strip()
        except Exception:
            new_email = request.POST.get('new_email', '').strip()
            
        if not new_email:
            return JsonResponse({'status': 'error', 'message': 'New email address cannot be empty.'})
                
        # Generate 6-digit OTP
        otp_val = str(random.randint(100000, 999999))
        
        # Save to session
        request.session['pending_new_email'] = new_email
        request.session['email_change_otp'] = otp_val
        request.session['email_change_otp_time'] = time.time()
        
        # Send mail
        subject = "FlixOra Email Change Verification OTP"
        body = f"Hello {request.user.username},\n\nWe received a request to change the email on your critic profile to: {new_email}.\n\nYour 6-digit verification code is: {otp_val}\nThis code is valid for 10 minutes."
        
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success', 'message': 'Verification code sent successfully to your new email.'})
        except Exception as e:
            print(f"Error sending email change OTP: {e}")
            if settings.DEBUG:
                return JsonResponse({
                    'status': 'success', 
                    'message': f'[TEST MODE] Code generated (Email sending failed): {otp_val}',
                    'test_otp': otp_val
                })
            return JsonResponse({'status': 'error', 'message': 'Failed to send verification email. Please check configuration.'})
            
    return JsonResponse({'status': 'error', 'message': 'POST request required.'}, status=400)

@login_required
def verify_email_change(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            otp_entered = data.get('otp_code', '').strip()
        except Exception:
            otp_entered = request.POST.get('otp_code', '').strip()
            
        if not otp_entered:
            return JsonResponse({'status': 'error', 'message': 'OTP code cannot be empty.'})
            
        saved_otp = request.session.get('email_change_otp')
        otp_time = request.session.get('email_change_otp_time', 0)
        pending_email = request.session.get('pending_new_email')
        
        if not saved_otp or not pending_email:
            return JsonResponse({'status': 'error', 'message': 'No pending email change request found.'})
            
        if time.time() - otp_time > 600:
            if 'email_change_otp' in request.session: del request.session['email_change_otp']
            if 'pending_new_email' in request.session: del request.session['pending_new_email']
            return JsonResponse({'status': 'error', 'message': 'Verification code has expired. Please try again.'})
            
        if otp_entered == saved_otp:
            user = request.user
            user.email = pending_email
            user.save()
            
            ActivityFeed.objects.create(user=user, action_text="changed email address successfully")
            
            del request.session['email_change_otp']
            del request.session['pending_new_email']
            if 'email_change_otp_time' in request.session: del request.session['email_change_otp_time']
            
            return JsonResponse({'status': 'success', 'message': 'Your email address has been updated successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid verification code. Please try again.'})
            
    return JsonResponse({'status': 'error', 'message': 'POST request required.'}, status=400)
