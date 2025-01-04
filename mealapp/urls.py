# mealapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add_recipe/', views.add_recipe, name='add_recipe'),
    path('view_recipes/', views.view_recipes, name='view_recipes'),
    path('meal_plan/', views.meal_plan, name='meal_plan'),
    path('grocery_list/', views.grocery_list, name='grocery_list'),
]
