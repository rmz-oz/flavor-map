from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Restaurant, Review, ReviewReply, UserProfile,
    MenuItem, RestaurantPhoto, OpeningHours
)


# ── Authentication Forms ─────────────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    """User registration with email and optional owner flag."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'})
    )
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
    is_owner = forms.BooleanField(
        required=False,
        label='Register as Restaurant Owner',
        help_text='Check this if you own or manage a restaurant.'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'password1', 'password2', 'is_owner']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email


class UserProfileForm(forms.ModelForm):
    """Edit bio, location and avatar on profile page."""
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell others about yourself...'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Istanbul, Turkey'}),
        }


# ── Restaurant Forms ─────────────────────────────────────────────────────────

class RestaurantForm(forms.ModelForm):
    """Create / Edit restaurant — MS3 ModelForm with validation."""
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'address', 'city', 'district',
            'phone', 'email', 'website', 'price_range', 'category',
            'latitude', 'longitude', 'main_photo',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Restaurant name'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe the restaurant, cuisine, atmosphere...'
            }),
            'address': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'district': forms.TextInput(attrs={'placeholder': 'District / Neighborhood (optional)'}),
            'phone': forms.TextInput(attrs={'placeholder': '+90 555 000 0000'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contact@restaurant.com'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://'}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '41.0082'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '28.9784'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise ValidationError('Restaurant name must be at least 2 characters.')
        return name

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if len(desc) < 20:
            raise ValidationError('Description must be at least 20 characters.')
        return desc


# ── Review Forms ─────────────────────────────────────────────────────────────

class ReviewForm(forms.ModelForm):
    """Review form used on the restaurant detail page."""
    rating = forms.IntegerField(
        widget=forms.HiddenInput(),
        min_value=1,
        max_value=5,
        error_messages={'required': 'Please select a star rating.'}
    )

    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your experience — food, service, atmosphere...',
                'class': 'form-control',
            }),
        }
        labels = {
            'text': 'Your Review',
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if len(text) < 10:
            raise ValidationError('Review must be at least 10 characters.')
        return text


class ReviewEditForm(forms.ModelForm):
    """Edit existing review — same fields as ReviewForm."""
    rating = forms.IntegerField(
        widget=forms.HiddenInput(),
        min_value=1,
        max_value=5,
    )

    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if len(text) < 10:
            raise ValidationError('Review must be at least 10 characters.')
        return text


class ReviewReplyForm(forms.ModelForm):
    """Reply to a review — single level nesting."""
    class Meta:
        model = ReviewReply
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Write a reply...',
                'class': 'form-control',
            }),
        }
        labels = {'text': ''}


# ── Menu & Photo Forms ───────────────────────────────────────────────────────

class MenuItemForm(forms.ModelForm):
    """Add / edit a menu item for a restaurant."""
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'category', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Item name'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Brief description'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price


class PhotoUploadForm(forms.ModelForm):
    """Upload a gallery photo for a restaurant."""
    class Meta:
        model = RestaurantPhoto
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Caption (optional)'}),
        }


# ── Search / Filter Form ─────────────────────────────────────────────────────

class SearchFilterForm(forms.Form):
    """Combined search + multi-filter form for the restaurant list page."""
    SORT_CHOICES = [
        ('',          'Default'),
        ('rating',    '⭐ Highest Rated'),
        ('newest',    '🆕 Newest First'),
        ('reviews',   '💬 Most Reviewed'),
        ('price_asc', '💸 Price: Low → High'),
        ('price_desc','💰 Price: High → Low'),
    ]
    RATING_CHOICES = [
        ('', 'Any Rating'),
        ('3', '3+ Stars'),
        ('4', '4+ Stars'),
        ('4.5', '4.5+ Stars'),
    ]

    q = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': '🔍 Search restaurants, cuisines, locations...',
            'class': 'form-control',
        })
    )
    category = forms.ChoiceField(required=False, choices=[], label='Category')
    city = forms.ChoiceField(required=False, choices=[], label='City')
    price_range = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Price'), ('€', '€'), ('€€', '€€'), ('€€€', '€€€')],
        label='Price'
    )
    min_rating = forms.ChoiceField(required=False, choices=RATING_CHOICES, label='Min Rating')
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, label='Sort By')
