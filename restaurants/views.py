"""
FlavorMap Views — covers:
  MS1 : function-based views with hardcoded context + URL routing
  MS2 : dynamic DB queries, model methods
  MS3 : forms, CRUD, auth, filtering, search
  Post : atomic transactions, photos, menu, favorites, profile, replies, likes
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import (
    Restaurant, Category, Review, ReviewReply, ReviewLike,
    Favorite, UserProfile, MenuItem, RestaurantPhoto, OpeningHours,
)
from .forms import (
    RegisterForm, RestaurantForm, ReviewForm, ReviewEditForm,
    ReviewReplyForm, MenuItemForm, PhotoUploadForm, SearchFilterForm,
    UserProfileForm,
)


# ════════════════════════════════════════════════════════════════
# MS1 — Static / Info Pages
# ════════════════════════════════════════════════════════════════

def about(request):
    """MS1 – static About page with hardcoded context."""
    context = {
        'page_title': 'About FlavorMap',
        'team_members': [
            {'name': 'Elif Arslan',  'role': 'Backend Developer',  'emoji': '👩‍💻'},
            {'name': 'Mert Kaya',    'role': 'Frontend Developer',  'emoji': '👨‍🎨'},
            {'name': 'Selin Demir',  'role': 'Database Architect',  'emoji': '👩‍🔬'},
        ],
        'stats': {
            'restaurants': Restaurant.objects.count(),
            'reviews':     Review.objects.count(),
            'users':       Review.objects.values('user').distinct().count(),
            'cities':      Restaurant.objects.values('city').distinct().count(),
        },
        'features': [
            '🔍 Discover restaurants by category, city & price',
            '⭐ Real reviews and star ratings from verified diners',
            '❤️  Build your personal favorites list',
            '🗺️  Map view for every restaurant',
            '📷 Photo galleries uploaded by the community',
            '🍴 Full menu listings with prices',
            '🏷️  Restaurant owners can claim and manage listings',
        ],
    }
    return render(request, 'restaurants/about.html', context)


def contact(request):
    """MS1 – static Contact page with hardcoded context."""
    submitted = False
    if request.method == 'POST':
        # In a real app this would send an email / save to DB
        submitted = True
        messages.success(request, '✅ Thanks for reaching out! We\'ll reply within 24 hours.')

    context = {
        'page_title': 'Contact Us',
        'submitted': submitted,
        'contact_info': {
            'email': 'hello@flavormap.com',
            'phone': '+90 212 555 0001',
            'address': 'İstiklal Caddesi 245, Beyoğlu, İstanbul',
            'hours': 'Mon–Fri, 09:00–18:00',
        },
        'faqs': [
            {'q': 'How do I add my restaurant?', 'a': 'Register an account, then click "Add Restaurant".'},
            {'q': 'Can I edit a review?',         'a': 'Yes — visit your profile page to edit or delete any of your reviews.'},
            {'q': 'How do I claim my listing?',   'a': 'On your restaurant\'s page, click "Claim this Restaurant".'},
            {'q': 'Is FlavorMap free?',           'a': 'Yes, completely free for diners and restaurant owners alike.'},
        ],
    }
    return render(request, 'restaurants/contact.html', context)


# ════════════════════════════════════════════════════════════════
# MS2 + Post — Homepage
# ════════════════════════════════════════════════════════════════

def home(request):
    """Homepage with top-rated and newest restaurants."""
    # Top rated (min 1 review)
    top_rated = (
        Restaurant.objects
        .annotate(avg_r=Avg('reviews__rating'), rev_count=Count('reviews'))
        .filter(rev_count__gt=0)
        .order_by('-avg_r', '-rev_count')[:6]
    )
    # Newest
    newest = Restaurant.objects.select_related('category').order_by('-created_at')[:6]
    # Categories with counts
    categories = (
        Category.objects
        .annotate(count=Count('restaurants'))
        .order_by('-count')
    )

    # MS1-style hardcoded hero stats for the banner
    hero_stats = {
        'restaurants': Restaurant.objects.count() or '100+',
        'reviews':     Review.objects.count() or '500+',
        'cities':      Restaurant.objects.values('city').distinct().count() or '10+',
    }

    context = {
        'page_title': 'Discover Great Restaurants',
        'top_rated': top_rated,
        'newest': newest,
        'categories': categories,
        'hero_stats': hero_stats,
    }
    return render(request, 'restaurants/home.html', context)


# ════════════════════════════════════════════════════════════════
# MS2 + MS3 — Restaurant List (with search + multi-filter)
# ════════════════════════════════════════════════════════════════

def restaurant_list(request):
    """
    MS1: basic list view
    MS2: dynamic DB queries
    MS3: search bar + category / city / price / rating multi-filter + sort
    """
    qs = Restaurant.objects.select_related('category').annotate(
        avg_r=Avg('reviews__rating'),
        rev_count=Count('reviews'),
    )

    # ── Build form with dynamic choices ──────────────────────────
    form = SearchFilterForm(request.GET or None)
    cities = Restaurant.objects.values_list('city', flat=True).distinct().order_by('city')
    categories_qs = Category.objects.all().order_by('name')
    form.fields['city'].choices = [('', 'All Cities')] + [(c, c) for c in cities]
    form.fields['category'].choices = [('', 'All Categories')] + [
        (cat.slug, f"{cat.icon} {cat.name}") for cat in categories_qs
    ]

    # ── Filtering ─────────────────────────────────────────────────
    q          = request.GET.get('q', '').strip()
    category   = request.GET.get('category', '')
    city       = request.GET.get('city', '')
    price      = request.GET.get('price_range', '')
    min_rating = request.GET.get('min_rating', '')
    sort       = request.GET.get('sort', '')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(city__icontains=q) |
            Q(address__icontains=q) |
            Q(district__icontains=q)
        )
    if category:
        qs = qs.filter(category__slug=category)
    if city:
        qs = qs.filter(city__iexact=city)
    if price:
        qs = qs.filter(price_range=price)
    if min_rating:
        qs = qs.filter(avg_r__gte=float(min_rating))

    # ── Sorting ───────────────────────────────────────────────────
    SORT_MAP = {
        'rating':     '-avg_r',
        'newest':     '-created_at',
        'reviews':    '-rev_count',
        'price_asc':  'price_range',
        'price_desc': '-price_range',
    }
    qs = qs.order_by(SORT_MAP.get(sort, '-created_at'))

    # ── Pagination ────────────────────────────────────────────────
    paginator = Paginator(qs, 12)
    page_obj  = paginator.get_page(request.GET.get('page'))

    # Strip page from GET params for pagination links
    get_copy = request.GET.copy()
    get_copy.pop('page', None)

    context = {
        'page_title':   'Discover Restaurants',
        'restaurants':  page_obj,
        'form':         form,
        'categories':   categories_qs,
        'cities':       cities,
        'total_count':  paginator.count,
        'query_string': get_copy.urlencode(),
        # Pass active filters back so we can show "active filter" badges
        'active_q':          q,
        'active_category':   category,
        'active_city':       city,
        'active_price':      price,
        'active_min_rating': min_rating,
        'active_sort':       sort,
    }
    return render(request, 'restaurants/restaurant_list.html', context)


# ════════════════════════════════════════════════════════════════
# MS2 + MS3 + Post — Restaurant Detail
# ════════════════════════════════════════════════════════════════

def restaurant_detail(request, pk):
    """
    Detail page: photos, menu, map, opening hours, reviews with
    replies, like/dislike, favorite toggle, review CRUD.
    """
    restaurant   = get_object_or_404(Restaurant, pk=pk)
    reviews      = restaurant.reviews.select_related('user').prefetch_related('replies__user', 'likes')
    menu_items   = restaurant.menu_items.filter(is_available=True).order_by('category', 'name')
    photos       = restaurant.photos.select_related('uploaded_by').all()
    opening_hrs  = restaurant.opening_hours.order_by('day')

    user_review  = None
    is_favorite  = False
    review_form  = ReviewForm()
    reply_form   = ReviewReplyForm()
    photo_form   = PhotoUploadForm()
    menu_form    = MenuItemForm()

    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            restaurant=restaurant, user=request.user
        ).first()
        is_favorite = Favorite.objects.filter(
            user=request.user, restaurant=restaurant
        ).exists()

    # ── POST handling ─────────────────────────────────────────────
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to continue.')
            return redirect('login')

        action = request.POST.get('action')

        # ── Submit review ─────────────────────────────────────────
        if action == 'submit_review':
            if user_review:
                messages.error(request, 'You have already reviewed this restaurant.')
            else:
                review_form = ReviewForm(request.POST)
                if review_form.is_valid():
                    try:
                        with transaction.atomic():
                            rev = review_form.save(commit=False)
                            rev.restaurant = restaurant
                            rev.user       = request.user
                            rev.save()
                        messages.success(request, '✅ Your review has been posted!')
                        return redirect('restaurant_detail', pk=pk)
                    except IntegrityError:
                        messages.error(request, 'You have already reviewed this restaurant.')
                else:
                    messages.error(request, 'Please fix the errors in your review.')

        # ── Post reply ────────────────────────────────────────────
        elif action == 'post_reply':
            review_id  = request.POST.get('review_id')
            target_rev = get_object_or_404(Review, pk=review_id, restaurant=restaurant)
            reply_form = ReviewReplyForm(request.POST)
            if reply_form.is_valid():
                with transaction.atomic():
                    rp = reply_form.save(commit=False)
                    rp.review = target_rev
                    rp.user   = request.user
                    rp.save()
                messages.success(request, 'Reply posted!')
                return redirect('restaurant_detail', pk=pk)

        # ── Upload photo ──────────────────────────────────────────
        elif action == 'upload_photo':
            photo_form = PhotoUploadForm(request.POST, request.FILES)
            if photo_form.is_valid():
                with transaction.atomic():
                    ph = photo_form.save(commit=False)
                    ph.restaurant   = restaurant
                    ph.uploaded_by  = request.user
                    ph.save()
                messages.success(request, '📸 Photo uploaded!')
                return redirect('restaurant_detail', pk=pk)

        # ── Add menu item (owner/staff only) ──────────────────────
        elif action == 'add_menu_item':
            is_mgr = (restaurant.owner == request.user or request.user.is_staff)
            if not is_mgr:
                messages.error(request, 'Only the restaurant owner can add menu items.')
            else:
                menu_form = MenuItemForm(request.POST)
                if menu_form.is_valid():
                    with transaction.atomic():
                        mi = menu_form.save(commit=False)
                        mi.restaurant = restaurant
                        mi.save()
                    messages.success(request, f'Menu item "{mi.name}" added!')
                    return redirect('restaurant_detail', pk=pk)

    # ── Group menu by category ────────────────────────────────────
    menu_by_cat = {}
    for item in menu_items:
        label = item.get_category_display()
        menu_by_cat.setdefault(label, []).append(item)

    # ── Related restaurants (same category, excluding self) ───────
    related = (
        Restaurant.objects
        .filter(category=restaurant.category)
        .exclude(pk=pk)
        .annotate(avg_r=Avg('reviews__rating'))
        .order_by('-avg_r')[:4]
    )

    context = {
        'page_title':   restaurant.name,
        'restaurant':   restaurant,
        'reviews':      reviews,
        'menu_by_cat':  menu_by_cat,
        'photos':       photos,
        'opening_hrs':  opening_hrs,
        'user_review':  user_review,
        'is_favorite':  is_favorite,
        'review_form':  review_form,
        'reply_form':   reply_form,
        'photo_form':   photo_form,
        'menu_form':    menu_form,
        'related':      related,
        'is_owner':     (restaurant.owner == request.user or request.user.is_staff)
                        if request.user.is_authenticated else False,
    }
    return render(request, 'restaurants/restaurant_detail.html', context)


# ════════════════════════════════════════════════════════════════
# MS3 — Restaurant CRUD
# ════════════════════════════════════════════════════════════════

@login_required
def restaurant_create(request):
    """Create a new restaurant (any logged-in user)."""
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    rest = form.save(commit=False)
                    # Set owner if user is registered as owner
                    profile = getattr(request.user, 'profile', None)
                    if profile and profile.is_owner:
                        rest.owner      = request.user
                        rest.is_claimed = True
                    rest.save()
                    # Auto-create 7-day opening hours scaffold
                    for day in range(7):
                        OpeningHours.objects.create(
                            restaurant=rest,
                            day=day,
                            open_time='12:00',
                            close_time='23:00',
                            is_closed=(day == 6),   # Sunday closed by default
                        )
                messages.success(request, f'🎉 "{rest.name}" has been added to FlavorMap!')
                return redirect('restaurant_detail', pk=rest.pk)
            except Exception as e:
                messages.error(request, f'Something went wrong: {e}')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RestaurantForm()

    return render(request, 'restaurants/restaurant_form.html', {
        'page_title': 'Add Restaurant',
        'form':       form,
        'action':     'Add',
    })


@login_required
def restaurant_edit(request, pk):
    """Edit a restaurant — only owner or staff."""
    restaurant = get_object_or_404(Restaurant, pk=pk)

    if restaurant.owner != request.user and not request.user.is_staff:
        messages.error(request, '🚫 You do not have permission to edit this restaurant.')
        return redirect('restaurant_detail', pk=pk)

    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, f'✅ "{restaurant.name}" updated successfully!')
            return redirect('restaurant_detail', pk=pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RestaurantForm(instance=restaurant)

    return render(request, 'restaurants/restaurant_form.html', {
        'page_title': f'Edit — {restaurant.name}',
        'form':        form,
        'action':      'Update',
        'restaurant':  restaurant,
    })


@login_required
def restaurant_delete(request, pk):
    """Delete confirmation page — POST only, owner or staff."""
    restaurant = get_object_or_404(Restaurant, pk=pk)

    if restaurant.owner != request.user and not request.user.is_staff:
        messages.error(request, '🚫 Permission denied.')
        return redirect('restaurant_detail', pk=pk)

    if request.method == 'POST':
        name = restaurant.name
        with transaction.atomic():
            restaurant.delete()
        messages.success(request, f'🗑️ "{name}" has been deleted.')
        return redirect('restaurant_list')

    return render(request, 'restaurants/restaurant_confirm_delete.html', {
        'page_title': f'Delete — {restaurant.name}',
        'restaurant': restaurant,
    })


# ════════════════════════════════════════════════════════════════
# MS3 — Review CRUD
# ════════════════════════════════════════════════════════════════

@login_required
def review_edit(request, pk):
    """Edit own review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ReviewEditForm(request.POST, instance=review)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, '✅ Review updated!')
            return redirect('restaurant_detail', pk=review.restaurant.pk)
    else:
        form = ReviewEditForm(instance=review)

    return render(request, 'restaurants/review_edit.html', {
        'page_title': 'Edit Review',
        'form':        form,
        'review':      review,
    })


@login_required
def review_delete(request, pk):
    """Delete own review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    restaurant_pk = review.restaurant.pk
    if request.method == 'POST':
        with transaction.atomic():
            review.delete()
        messages.success(request, '🗑️ Review deleted.')
        return redirect('restaurant_detail', pk=restaurant_pk)
    return render(request, 'restaurants/review_confirm_delete.html', {
        'page_title': 'Delete Review',
        'review': review,
    })


# ════════════════════════════════════════════════════════════════
# Post-MS3 — Favorites (AJAX-friendly)
# ════════════════════════════════════════════════════════════════

@login_required
def toggle_favorite(request, pk):
    """Add or remove a restaurant from favorites. Supports AJAX."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    is_fav = False
    try:
        with transaction.atomic():
            fav, created = Favorite.objects.get_or_create(
                user=request.user, restaurant=restaurant
            )
            if not created:
                fav.delete()
                is_fav = False
            else:
                is_fav = True
    except IntegrityError:
        is_fav = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_fav})
    action_text = 'added to' if is_fav else 'removed from'
    messages.success(request, f'"{restaurant.name}" {action_text} your favorites.')
    return redirect('restaurant_detail', pk=pk)


# ════════════════════════════════════════════════════════════════
# Post-MS3 — Review Likes (AJAX)
# ════════════════════════════════════════════════════════════════

@login_required
def like_review(request, pk):
    """Toggle like or dislike on a review. Always returns JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    review  = get_object_or_404(Review, pk=pk)
    is_like = request.POST.get('is_like') == 'true'

    try:
        with transaction.atomic():
            like_obj, created = ReviewLike.objects.get_or_create(
                review=review, user=request.user,
                defaults={'is_like': is_like}
            )
            if not created:
                if like_obj.is_like == is_like:
                    # Same button clicked again → remove
                    like_obj.delete()
                else:
                    # Switch like↔dislike
                    like_obj.is_like = is_like
                    like_obj.save()
    except IntegrityError:
        pass

    return JsonResponse({
        'likes':    review.like_count(),
        'dislikes': review.dislike_count(),
    })


# ════════════════════════════════════════════════════════════════
# Post-MS3 — Owner: Menu CRUD & Restaurant Claim
# ════════════════════════════════════════════════════════════════

@login_required
def menu_item_delete(request, pk):
    """Delete a menu item — owner or staff only."""
    item = get_object_or_404(MenuItem, pk=pk)
    if item.restaurant.owner != request.user and not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('restaurant_detail', pk=item.restaurant.pk)
    if request.method == 'POST':
        rest_pk = item.restaurant.pk
        with transaction.atomic():
            item.delete()
        messages.success(request, 'Menu item deleted.')
        return redirect('restaurant_detail', pk=rest_pk)
    return render(request, 'restaurants/menu_item_confirm_delete.html', {'item': item})


@login_required
def claim_restaurant(request, pk):
    """Claim an unclaimed restaurant listing."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if restaurant.is_claimed:
        messages.warning(request, 'This restaurant has already been claimed.')
        return redirect('restaurant_detail', pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.is_owner = True
            profile.save()
            restaurant.owner      = request.user
            restaurant.is_claimed = True
            restaurant.save()
        messages.success(request, f'🏷️ You are now the verified owner of "{restaurant.name}"!')
        return redirect('restaurant_detail', pk=pk)

    return render(request, 'restaurants/claim_restaurant.html', {
        'page_title': f'Claim — {restaurant.name}',
        'restaurant': restaurant,
    })


# ════════════════════════════════════════════════════════════════
# Post-MS3 — User Profile
# ════════════════════════════════════════════════════════════════

@login_required
def profile(request):
    """User profile page — reviews, favorites, owned restaurants."""
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    profile_form   = UserProfileForm(instance=profile_obj)

    if request.method == 'POST' and request.POST.get('action') == 'update_profile':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile_obj)
        if profile_form.is_valid():
            with transaction.atomic():
                profile_form.save()
            messages.success(request, '✅ Profile updated!')
            return redirect('profile')

    user_reviews = (
        Review.objects
        .filter(user=request.user)
        .select_related('restaurant')
        .order_by('-created_at')
    )
    favorites = (
        Favorite.objects
        .filter(user=request.user)
        .select_related('restaurant__category')
        .order_by('-added_at')
    )
    owned = Restaurant.objects.filter(owner=request.user).annotate(
        avg_r=Avg('reviews__rating'), rev_count=Count('reviews')
    )

    context = {
        'page_title':    f'{request.user.username} — Profile',
        'profile_obj':   profile_obj,
        'profile_form':  profile_form,
        'user_reviews':  user_reviews,
        'favorites':     favorites,
        'owned':         owned,
    }
    return render(request, 'restaurants/profile.html', context)


# ════════════════════════════════════════════════════════════════
# MS3 — Authentication
# ════════════════════════════════════════════════════════════════

def register_view(request):
    """User registration form with owner role option."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    is_owner = form.cleaned_data.get('is_owner', False)
                    UserProfile.objects.create(user=user, is_owner=is_owner)
                login(request, user)
                messages.success(request, f'🎉 Welcome to FlavorMap, {user.username}!')
                return redirect('home')
            except IntegrityError:
                messages.error(request, 'Registration failed. Please try again.')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'restaurants/register.html', {
        'page_title': 'Create Account',
        'form': form,
    })


def login_view(request):
    """Login with Django's AuthenticationForm."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'👋 Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'restaurants/login.html', {
        'page_title': 'Login',
        'form': form,
    })


def logout_view(request):
    """Logout and redirect to home."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')
