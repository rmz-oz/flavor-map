from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils import timezone


class Category(models.Model):
    """Restaurant cuisine category (Turkish, Italian, Fast Food, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, default='🍽️')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}"

    def restaurant_count(self):
        return self.restaurants.count()


class Restaurant(models.Model):
    """Main restaurant entity with all core fields."""
    PRICE_CHOICES = [
        ('€',   '€ — Budget-friendly'),
        ('€€',  '€€ — Mid-range'),
        ('€€€', '€€€ — Fine Dining'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    price_range = models.CharField(max_length=5, choices=PRICE_CHOICES, default='€€')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        related_name='restaurants'
    )
    # Owner / claiming
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='owned_restaurants'
    )
    is_claimed = models.BooleanField(default=False)
    # Location for map embed
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Photo
    main_photo = models.ImageField(upload_to='restaurants/main/', blank=True, null=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # ── Computed properties ──────────────────────────────────────────────────

    def average_rating(self):
        """Return average star rating rounded to 1 decimal."""
        result = self.reviews.aggregate(avg=Avg('rating'))
        return round(result['avg'] or 0, 1)

    def review_count(self):
        return self.reviews.count()

    def star_display(self):
        """Return dict with full/half/empty counts for template rendering."""
        avg = self.average_rating()
        full = int(avg)
        half = 1 if (avg - full) >= 0.5 else 0
        empty = 5 - full - half
        return {
            'full': range(full),
            'half': range(half),
            'empty': range(empty),
            'avg': avg,
        }

    def get_price_label(self):
        return dict(self.PRICE_CHOICES).get(self.price_range, self.price_range)


class RestaurantPhoto(models.Model):
    """Gallery photos for a restaurant (multiple per restaurant)."""
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='photos'
    )
    image = models.ImageField(upload_to='restaurants/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Photo for {self.restaurant.name}"


class OpeningHours(models.Model):
    """Operating hours per day of the week for a restaurant."""
    DAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='opening_hours'
    )
    day = models.IntegerField(choices=DAYS)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['day']
        unique_together = ['restaurant', 'day']

    def __str__(self):
        day_name = dict(self.DAYS).get(self.day, 'Unknown')
        if self.is_closed:
            return f"{self.restaurant.name} – {day_name}: Closed"
        return f"{self.restaurant.name} – {day_name}: {self.open_time}–{self.close_time}"

    def day_name(self):
        return dict(self.DAYS).get(self.day, '')


class MenuItem(models.Model):
    """Menu item belonging to a restaurant."""
    MENU_CATEGORIES = [
        ('starter',  'Starters & Appetizers'),
        ('soup',     'Soups'),
        ('salad',    'Salads'),
        ('main',     'Main Course'),
        ('grill',    'Grills & BBQ'),
        ('pasta',    'Pasta & Rice'),
        ('pizza',    'Pizza'),
        ('dessert',  'Desserts'),
        ('drinks',   'Beverages'),
        ('other',    'Other'),
    ]
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='menu_items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20, choices=MENU_CATEGORIES, default='main')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (€{self.price}) – {self.restaurant.name}"


class Review(models.Model):
    """Diner review with star rating (1–5) and text."""
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['restaurant', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.restaurant.name} ({self.rating}★)"

    def star_display(self):
        return {
            'full': range(self.rating),
            'empty': range(5 - self.rating),
        }

    def like_count(self):
        return self.likes.filter(is_like=True).count()

    def dislike_count(self):
        return self.likes.filter(is_like=False).count()

    def helpful_score(self):
        return self.like_count() - self.dislike_count()


class ReviewReply(models.Model):
    """Single-level reply to a review (owner or other users)."""
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='replies'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} replied to review #{self.review.pk}"


class ReviewLike(models.Model):
    """Like or dislike on a review — one per user per review."""
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='likes'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_likes')
    is_like = models.BooleanField(default=True)  # True=like, False=dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['review', 'user']

    def __str__(self):
        action = 'liked' if self.is_like else 'disliked'
        return f"{self.user.username} {action} review #{self.review.pk}"


class Favorite(models.Model):
    """A user's saved/favorited restaurant."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='favorited_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'restaurant']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} ♥ {self.restaurant.name}"


class UserProfile(models.Model):
    """Extended profile attached 1-to-1 with Django's User model."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_owner = models.BooleanField(default=False)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"

    def total_reviews(self):
        return self.user.reviews.count()

    def total_favorites(self):
        return self.user.favorites.count()
