from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('places/', views.places, name="places"),
    path('status/', views.status_view, name="status"),
    path('leaderboard/', views.get_leaderboard, name="leaderboard"),
    path('map/', views.map_view, name="map"),
    path('hi/', views.say_hello_view, name="say_hello"),
    path('tp/', views.teleport, name="teleport"),
]