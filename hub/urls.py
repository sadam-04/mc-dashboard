from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('places/', views.places, name="places"),
    path('map/', views.map, name="map"),
    path('hi/', views.say_hello, name="say_hello"),
    path('tp/', views.teleport, name="teleport"),
]