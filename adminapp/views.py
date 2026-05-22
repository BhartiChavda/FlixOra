from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from userapp.models import Movie, Review, Rating, Profile
from userapp.forms import MovieForm

# Add Admin CRUD
@login_required
def add_movie(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            m = form.save()
            messages.success(request, f"Movie {m.title} added successfully!")
            return redirect('admin_dashboard')
    else:
        form = MovieForm()
    return render(request, 'admin/movie_form.html', {'form': form, 'title': 'Add Movie'})

@login_required
def edit_movie(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {movie.title}!")
            return redirect('movie_detail', pk=pk)
    else:
        form = MovieForm(instance=movie)
    return render(request, 'admin/movie_form.html', {'form': form, 'title': f'Edit {movie.title}', 'movie': movie})

@login_required
def delete_movie(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        movie.delete()
        messages.success(request, "Movie deleted.")
        return redirect('admin_dashboard')
    return render(request, 'admin/movie_confirm_delete.html', {'movie': movie})

def admin_dashboard(request):
    # If already logged in as staff/superuser
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        # Stats
        total_movies = Movie.objects.count()
        total_users = User.objects.count()
        total_reviews = Review.objects.count()
        total_ratings = Rating.objects.count()
        
        # Media type breakdowns
        media_breakdown = Movie.objects.values('media_type').annotate(count=Count('id'))
        media_stats = {
            'movie': 0,
            'tv_show': 0,
            'web_series': 0,
            'ott': 0,
            'documentary': 0,
            'anime': 0,
        }
        for item in media_breakdown:
            mtype = item['media_type']
            if mtype in media_stats:
                media_stats[mtype] = item['count']
                
        # Search / Filters
        movie_query = request.GET.get('movie_search', '')
        user_query = request.GET.get('user_search', '')
        
        if movie_query:
            movies = Movie.objects.filter(title__icontains=movie_query)
        else:
            movies = Movie.objects.all().order_by('-id')
            
        if user_query:
            users = User.objects.select_related('profile').filter(username__icontains=user_query)
        else:
            users = User.objects.select_related('profile').all().order_by('-date_joined')
            
        reviews = Review.objects.select_related('user', 'movie').all().order_by('-id')[:30] # recent 30 reviews
        
        context = {
            'total_movies': total_movies,
            'total_users': total_users,
            'total_reviews': total_reviews,
            'total_ratings': total_ratings,
            'media_stats': media_stats,
            'movies': movies,
            'users': users,
            'reviews': reviews,
            'movie_query': movie_query,
            'user_query': user_query,
        }
        return render(request, 'admin/dashboard.html', context)

    # If NOT logged in as staff/superuser
    if request.user.is_authenticated:
        messages.error(request, "Access Denied: You do not have administrator permissions.")
        return redirect('dashboard')

    if request.method == 'POST':
        username_val = request.POST.get('username')
        password_val = request.POST.get('password')
        user = authenticate(request, username=username_val, password=password_val)
        if user is not None:
            if user.is_staff or user.is_superuser:
                auth_login(request, user)
                messages.success(request, f"Welcome back, Admin {user.username}!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Access Denied: You do not have administrator permissions.")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'admin/login.html')

@login_required
def toggle_verification(request, user_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    target_user = get_object_or_404(User, pk=user_id)
    profile, created = Profile.objects.get_or_create(user=target_user)
    profile.verified = not profile.verified
    profile.save()
    
    return JsonResponse({
        'status': 'success',
        'verified': profile.verified,
        'message': f"User verification status updated!"
    })

@login_required
def delete_review(request, review_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    review = get_object_or_404(Review, pk=review_id)
    movie_title = review.movie.title
    review.delete()
    messages.success(request, f"Review on {movie_title} deleted successfully.")
    return redirect('admin_dashboard')

@login_required
def delete_user(request, user_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    target_user = get_object_or_404(User, pk=user_id)
    if target_user.is_superuser:
        messages.error(request, "Cannot delete superuser.")
        return redirect('admin_dashboard')
    username = target_user.username
    target_user.delete()
    messages.success(request, f"User {username} deleted successfully.")
    return redirect('admin_dashboard')
