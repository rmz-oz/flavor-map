"""
FlavorMap URL patterns
  MS1 requirement: at least 5 named URL patterns
    1. home
    2. restaurant_list
    3. restaurant_detail
    4. about
    5. contact
  + all MS2/MS3/Post CRUD and auth URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── MS1: Core static/info pages ──────────────────────────────
    path('',           views.home,            name='home'),
    path('about/',     views.about,           name='about'),
    path('contact/',   views.contact,         name='contact'),

    # ── MS1: Restaurant browsing ──────────────────────────────────
    path('restaurants/',            views.restaurant_list,   name='restaurant_list'),
    path('restaurants/<int:pk>/',   views.restaurant_detail, name='restaurant_detail'),

    # ── MS3: Restaurant CRUD ──────────────────────────────────────
    path('restaurants/add/',               views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/edit/',     views.restaurant_edit,   name='restaurant_edit'),
    path('restaurants/<int:pk>/delete/',   views.restaurant_delete, name='restaurant_delete'),

    # ── MS3: Review CRUD ──────────────────────────────────────────
    path('reviews/<int:pk>/edit/',         views.review_edit,   name='review_edit'),
    path('reviews/<int:pk>/delete/',       views.review_delete, name='review_delete'),

    # ── Post: Favorites, likes, claim ────────────────────────────
    path('restaurants/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('restaurants/<int:pk>/claim/',    views.claim_restaurant, name='claim_restaurant'),
    path('reviews/<int:pk>/like/',         views.like_review,     name='like_review'),

    # ── Post: Menu item delete ────────────────────────────────────
    path('menu-item/<int:pk>/delete/',     views.menu_item_delete, name='menu_item_delete'),

    # ── Post: User profile ────────────────────────────────────────
    path('profile/', views.profile, name='profile'),

    # ── MS3: Authentication ───────────────────────────────────────
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),
]
