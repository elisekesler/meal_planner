# mealapp/urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add_recipe/', views.add_recipe, name='add_recipe'),
    path('view_recipes/', views.view_recipes, name='view_recipes'),
    path('meal_plan/', views.meal_plan_view, name='meal_plan'),
    path("add_ingredient/", views.add_ingredient, name="add_ingredient"),
    path("view_ingredients/", views.view_ingredients, name="view_ingredients"),
    path("api/ingredient/<str:ingredient_name>/", views.ingredient_detail, name="ingredient_detail"),
    path('generate-grocery-list/', views.generate_grocery_list, name='generate_grocery_list'),
    path('api/check-ingredient/<str:name>/', views.check_ingredient, name='check-ingredient'),
    path('api/ingredients/', views.add_ingredient, name='add-ingredient'),
    path('delete-ingredient/<int:ingredient_id>/', views.delete_ingredient, name='delete_ingredient'),
    path('delete-recipe/<int:recipe_id>/', views.delete_recipe, name='delete_recipe'),
    path('api/add-to-meal-plan/', views.add_to_meal_plan, name='add-to-meal-plan'),
    path('unit-conversions/', views.manage_unit_conversions, name='unit_conversions'),
    path('test-conversion/', views.test_conversion, name='test_conversion'),
]
