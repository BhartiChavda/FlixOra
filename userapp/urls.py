from django.urls import path
from . import views

urlpatterns = [
    # Core
    path('', views.dashboard, name='dashboard'),
    path('movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('recommend/', views.mood_recommendation, name='mood_recommendation'),
    
    # Social Interactions (AJAX)
    path('like/toggle/', views.toggle_like, name='toggle_like'),
    path('bookmark/toggle/', views.toggle_bookmark, name='toggle_bookmark'),
    path('review/<int:review_id>/comment/add/', views.add_comment, name='add_comment'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('user/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('user/<str:username>/connections/json/', views.user_connections_json, name='user_connections_json'),
    
    # Social Feeds
    path('feed/following/', views.following_feed, name='following_feed'),
    path('feed/activity/', views.global_activity_feed, name='activity_feed'),
    path('notifications/', views.notifications_view, name='notifications'),
    
    # Search
    path('search/', views.search_filter, name='search_filter'),
    
    # Profile (Public Critic profile)
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    
    # Auth
    path('register/', views.register_user, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-email/request/', views.request_email_change, name='request_email_change'),
    path('change-email/verify/', views.verify_email_change, name='verify_email_change'),
]
