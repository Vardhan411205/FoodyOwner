from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.index, name='index'),
    path('quick-bite/', views.quick_bite, name='quick_bite'),
    path('all-tables/', views.all_tables, name='all_tables'),
    path('profile/', views.edit_profile, name='edit_profile'),
] 