from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/toggle-verification/<int:user_id>/', views.toggle_verification, name='admin_toggle_verification'),
    path('admin/delete-review/<int:review_id>/', views.delete_review, name='admin_delete_review'),
    path('admin/delete-user/<int:user_id>/', views.delete_user, name='admin_delete_user'),
    path('movie/add/', views.add_movie, name='add_movie'),
    path('movie/<int:pk>/edit/', views.edit_movie, name='edit_movie'),
    path('movie/<int:pk>/delete/', views.delete_movie, name='delete_movie'),
]
