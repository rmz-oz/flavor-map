from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Restaurant, RestaurantPhoto, OpeningHours,
    MenuItem, Review, ReviewReply, ReviewLike, Favorite, UserProfile,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['icon', 'name', 'slug', 'restaurant_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    def restaurant_count(self, obj):
        return obj.restaurants.count()
    restaurant_count.short_description = 'Restaurants'


class RestaurantPhotoInline(admin.TabularInline):
    model  = RestaurantPhoto
    extra  = 1
    fields = ['image', 'caption', 'uploaded_by']
    readonly_fields = ['uploaded_at']


class OpeningHoursInline(admin.TabularInline):
    model  = OpeningHours
    extra  = 0
    fields = ['day', 'open_time', 'close_time', 'is_closed']


class MenuItemInline(admin.TabularInline):
    model  = MenuItem
    extra  = 2
    fields = ['name', 'category', 'price', 'is_available']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display   = [
        'name', 'city', 'district', 'category',
        'price_range', 'avg_rating_display', 'review_count_display',
        'is_claimed', 'created_at',
    ]
    list_filter    = ['category', 'price_range', 'city', 'is_claimed', 'created_at']
    search_fields  = ['name', 'description', 'city', 'address', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines        = [MenuItemInline, OpeningHoursInline, RestaurantPhotoInline]
    fieldsets = [
        ('Basic Info', {
            'fields': ('name', 'description', 'category', 'price_range')
        }),
        ('Contact & Location', {
            'fields': ('address', 'city', 'district', 'phone', 'email', 'website',
                       'latitude', 'longitude')
        }),
        ('Ownership', {
            'fields': ('owner', 'is_claimed')
        }),
        ('Media', {
            'fields': ('main_photo',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    ]

    def avg_rating_display(self, obj):
        avg = obj.average_rating()
        if avg:
            stars = '⭐' * int(round(avg))
            return format_html(f'<span title="{avg}">{stars} {avg}</span>')
        return '—'
    avg_rating_display.short_description = 'Avg Rating'

    def review_count_display(self, obj):
        return obj.review_count()
    review_count_display.short_description = 'Reviews'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['user', 'restaurant', 'rating', 'like_count', 'created_at']
    list_filter   = ['rating', 'created_at']
    search_fields = ['user__username', 'restaurant__name', 'text']
    readonly_fields = ['created_at', 'updated_at']

    def like_count(self, obj):
        return obj.like_count()
    like_count.short_description = 'Likes'


@admin.register(ReviewReply)
class ReviewReplyAdmin(admin.ModelAdmin):
    list_display  = ['user', 'review', 'created_at']
    search_fields = ['user__username', 'text']


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'review', 'is_like', 'created_at']
    list_filter  = ['is_like']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ['name', 'restaurant', 'category', 'price', 'is_available']
    list_filter   = ['category', 'is_available', 'restaurant']
    search_fields = ['name', 'restaurant__name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display  = ['user', 'restaurant', 'added_at']
    search_fields = ['user__username', 'restaurant__name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'is_owner', 'location', 'created_at']
    list_filter   = ['is_owner']
    search_fields = ['user__username', 'user__email']


@admin.register(OpeningHours)
class OpeningHoursAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'day', 'open_time', 'close_time', 'is_closed']
    list_filter  = ['day', 'is_closed']


admin.site.site_header = '🍽️ FlavorMap Admin'
admin.site.site_title  = 'FlavorMap'
admin.site.index_title = 'Restaurant Management Dashboard'
