"""
python manage.py seed_data

Seeds the database with:
  - 6 categories
  - 3 demo users (admin, owner1, reviewer1)
  - 8 restaurants across different cities/categories
  - Menu items for each restaurant
  - Opening hours for each restaurant
  - Sample reviews with replies and likes
  - Favorites
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal

from restaurants.models import (
    Category, Restaurant, MenuItem, OpeningHours,
    Review, ReviewReply, ReviewLike, Favorite, UserProfile,
)


CATEGORIES = [
    ('Turkish',       'turkish',    '🥙'),
    ('Italian',       'italian',    '🍝'),
    ('Seafood',       'seafood',    '🦞'),
    ('Fast Food',     'fastfood',   '🍔'),
    ('Vegetarian',    'vegetarian', '🥗'),
    ('Fine Dining',   'fine-dining','🍷'),
]

RESTAURANTS = [
    {
        'name': 'Garden 1897',
        'city': 'Istanbul', 'district': 'Sultanahmet',
        'description': 'A historic garden restaurant serving authentic Turkish cuisine since 1897. Famous for its warm hospitality, generous mezes, complimentary baklava, and refreshing pomegranate juice served in a beautifully decorated courtyard.',
        'address': 'Küçük Ayasofya, Şht. Mehmetpaşa Sok. No5, Fatih',
        'phone': '+90 530 186 23 59',
        'price_range': '€€', 'category': 'turkish',
        'lat': Decimal('41.004025'), 'lng': Decimal('28.972559'),
        'menu': [
            ('Mercimek Çorbası', 'Classic red lentil soup with lemon', Decimal('8.00'), 'starter'),
            ('Hummus',           'House-made with tahini and olive oil', Decimal('10.00'), 'starter'),
            ('Izgara Köfte',     'Grilled meatballs with bulgur pilav',  Decimal('22.00'), 'main'),
            ('Lamb Chops',       'Tender grilled lamb with couscous',    Decimal('38.00'), 'main'),
            ('Baklava',          'Honey and pistachio pastry',           Decimal('12.00'), 'dessert'),
            ('Ayran',            'Traditional cold yogurt drink',        Decimal('5.00'),  'drinks'),
            ('Pomegranate Juice','Freshly squeezed',                     Decimal('8.00'),  'drinks'),
        ],
    },
    {
        'name': 'Hidden Garden Sultanahmet',
        'city': 'Istanbul', 'district': 'Sultanahmet',
        'description': 'A peaceful oasis tucked away from the bustling streets of Istanbul. Known for exceptional stuffed calamari, perfectly cooked lamb chops, and an enchanting garden atmosphere. Complimentary starters and baklava included.',
        'address': 'Binbirdirek, Peykhane Cd. No: 14/A, Fatih',
        'phone': '+90 534 927 53 47',
        'price_range': '€€', 'category': 'turkish',
        'lat': Decimal('41.006749'), 'lng': Decimal('28.972428'),
        'menu': [
            ('Stuffed Calamari',  'Signature dish — beautifully cooked',    Decimal('28.00'), 'starter'),
            ('Lamb Chops',        'Juicy, spice-forward with couscous',      Decimal('40.00'), 'main'),
            ('Moussaka',          'Layers of aubergine and spiced mince',    Decimal('24.00'), 'main'),
            ('Tiramisu',          'Italian classic with a Turkish twist',    Decimal('14.00'), 'dessert'),
            ('Turkish Tea',       'Complimentary on house',                  Decimal('0.00'),  'drinks'),
        ],
    },
    {
        'name': 'Pleasure Terrace Rooftop',
        'city': 'Istanbul', 'district': 'Eminönü',
        'description': 'Stunning rooftop views of Istanbul with a warm, soulful atmosphere. Fresh Turkish cuisine with an authentic home-cooked feeling. Take the elevator to the 5th floor for panoramic views of the historic peninsula.',
        'address': 'Hoca Paşa, Hüdavendigar Cd. No:4 Kat:5',
        'phone': '+90 539 377 07 43',
        'price_range': '€€', 'category': 'turkish',
        'lat': Decimal('41.012609'), 'lng': Decimal('28.978357'),
        'menu': [
            ('Mushroom Casserole', 'Sautéed mushrooms in cream sauce',   Decimal('18.00'), 'starter'),
            ('Chicken Casserole',  'Slow-roasted chicken with vegetables',Decimal('26.00'), 'main'),
            ('Ravioli',            'House-made with butter sage sauce',   Decimal('22.00'), 'pasta'),
            ('Lamb Skewer',        'Tender grilled with roasted pepper',  Decimal('32.00'), 'grill'),
            ('Baklava + Tea',      'Complimentary to finish your meal',   Decimal('0.00'),  'dessert'),
        ],
    },
    {
        'name': 'Napoli Vera',
        'city': 'Istanbul', 'district': 'Beyoğlu',
        'description': 'Authentic Neapolitan pizza and pasta in the vibrant heart of Beyoğlu. Our dough ferments for 48 hours, baked in a wood-fired oven imported from Naples. Ingredients flown in weekly from Italy.',
        'address': 'İstiklal Caddesi 245, Beyoğlu',
        'phone': '+90 212 555 0123',
        'price_range': '€€', 'category': 'italian',
        'lat': Decimal('41.033000'), 'lng': Decimal('28.978000'),
        'menu': [
            ('Bruschetta',       'Tomato, basil, extra virgin olive oil',     Decimal('9.00'),  'starter'),
            ('Margherita Pizza', 'San Marzano tomato, fior di latte',         Decimal('18.00'), 'pizza'),
            ('Diavola Pizza',    'Spicy salami, chilli, mozzarella',          Decimal('22.00'), 'pizza'),
            ('Cacio e Pepe',     'Spaghetti, pecorino, black pepper',         Decimal('20.00'), 'pasta'),
            ('Tiramisu',         'Savoiardi, mascarpone, espresso',           Decimal('12.00'), 'dessert'),
            ('Espresso',         'Italian blend, double shot',                Decimal('5.00'),  'drinks'),
        ],
    },
    {
        'name': 'Bosphorus Seafood',
        'city': 'Istanbul', 'district': 'Beşiktaş',
        'description': 'Fresh catch daily from the Bosphorus Strait. Stunning sea views and expertly prepared fish and seafood. A must-visit for anyone who loves the sea.',
        'address': 'Çırağan Cd. 10, Beşiktaş',
        'phone': '+90 212 555 0456',
        'price_range': '€€€', 'category': 'seafood',
        'lat': Decimal('41.044000'), 'lng': Decimal('29.005000'),
        'menu': [
            ('Calamari',         'Lightly battered, served with aioli',      Decimal('18.00'), 'starter'),
            ('Octopus Salad',    'Grilled octopus, lemon, capers',            Decimal('22.00'), 'starter'),
            ('Grilled Sea Bass', 'Whole fish, roasted vegetables',            Decimal('45.00'), 'main'),
            ('Lobster',          'Market price — ask your server',            Decimal('90.00'), 'main'),
            ('Crème Brûlée',     'Classic vanilla with caramelised top',     Decimal('16.00'), 'dessert'),
            ('White Wine',       'Chardonnay, 150ml',                        Decimal('18.00'), 'drinks'),
        ],
    },
    {
        'name': 'Green Bowl',
        'city': 'Ankara', 'district': 'Çankaya',
        'description': 'A fresh, plant-powered café in the heart of Çankaya. All dishes are 100% vegetarian with many vegan options. Locally sourced seasonal ingredients.',
        'address': 'Tunalı Hilmi Cad. 78, Çankaya',
        'phone': '+90 312 555 0789',
        'price_range': '€', 'category': 'vegetarian',
        'lat': Decimal('39.906900'), 'lng': Decimal('32.862500'),
        'menu': [
            ('Lentil Soup',      'Red lentil with cumin and lemon',           Decimal('7.00'),  'soup'),
            ('Buddha Bowl',      'Grains, roasted veg, tahini dressing',      Decimal('18.00'), 'main'),
            ('Falafel Wrap',     'House falafel, hummus, tabbouleh',          Decimal('14.00'), 'main'),
            ('Avocado Toast',    'Sourdough, smashed avo, chilli flakes',     Decimal('13.00'), 'main'),
            ('Matcha Latte',     'Ceremonial grade matcha, oat milk',         Decimal('7.00'),  'drinks'),
        ],
    },
    {
        'name': 'Burger Republic',
        'city': 'Izmir', 'district': 'Alsancak',
        'description': 'The best smash burgers in Izmir. Fresh-ground beef, brioche buns baked daily, house-made sauces. Fast, satisfying, and surprisingly affordable.',
        'address': 'Kıbrıs Şehitleri Cad. 55, Alsancak',
        'phone': '+90 232 555 0321',
        'price_range': '€', 'category': 'fastfood',
        'lat': Decimal('38.437700'), 'lng': Decimal('27.144000'),
        'menu': [
            ('Classic Smash',    'Double patty, American cheese, pickles',    Decimal('14.00'), 'main'),
            ('BBQ Bacon Smash',  'Crispy bacon, BBQ sauce, caramelised onion',Decimal('18.00'), 'main'),
            ('Veggie Smash',     'Plant-based patty, all the trimmings',      Decimal('14.00'), 'main'),
            ('Fries',            'Skin-on, seasoned with paprika salt',       Decimal('6.00'),  'other'),
            ('Milkshake',        'Vanilla, chocolate or strawberry',          Decimal('8.00'),  'drinks'),
        ],
    },
    {
        'name': 'Ristorante La Dolce Vita',
        'city': 'Ankara', 'district': 'Kavaklıdere',
        'description': 'Elegant Italian fine dining with an extensive wine list and impeccable service. Perfect for business dinners, anniversaries, and special celebrations.',
        'address': 'Arjantin Cad. 24, Kavaklıdere',
        'phone': '+90 312 555 0654',
        'price_range': '€€€', 'category': 'fine-dining',
        'lat': Decimal('39.900500'), 'lng': Decimal('32.863200'),
        'menu': [
            ('Beef Carpaccio',   'Truffle oil, parmesan, rocket',             Decimal('28.00'), 'starter'),
            ('Lobster Bisque',   'Creamy, with cognac and cream',             Decimal('22.00'), 'soup'),
            ('Ossobuco',         'Braised veal shank, saffron risotto',       Decimal('65.00'), 'main'),
            ('Black Truffle Pasta','Tagliolini with black truffle, butter',   Decimal('55.00'), 'pasta'),
            ('Panna Cotta',      'Vanilla, seasonal berry coulis',            Decimal('18.00'), 'dessert'),
            ('Barolo 2018',      'Glass, 150ml',                              Decimal('28.00'), 'drinks'),
        ],
    },
]

REVIEWS = [
    # (restaurant_name, username, rating, text)
    ('Garden 1897', 'foodlover',
     5, 'Absolutely wonderful! The lamb chops were perfectly cooked and the staff were so warm. The complimentary baklava and tea at the end were a lovely touch. I will definitely be back next time I\'m in Istanbul.'),
    ('Garden 1897', 'gourmet_explorer',
     4, 'Great atmosphere in a lovely courtyard setting. Food is authentic Turkish with generous portions. Slightly on the expensive side but worth it for the experience.'),
    ('Hidden Garden Sultanahmet', 'foodlover',
     5, 'Truly a hidden gem! We stumbled upon this place and were blown away. The stuffed calamari is a must-order. Service was excellent and the garden seating is magical at night.'),
    ('Hidden Garden Sultanahmet', 'hungry_traveller',
     5, 'One of the best meals of our entire trip to Turkey. Fresh, flavourful and beautifully presented. The free starters and baklava were a lovely surprise.'),
    ('Pleasure Terrace Rooftop', 'gourmet_explorer',
     5, 'The views alone are worth the trip but the food exceeds expectations too. Very home-cooked feeling. Sit outside on a warm evening for the full experience.'),
    ('Napoli Vera', 'foodlover',
     4, 'Excellent pizza — possibly the best in Istanbul. The wood-fired crust is perfectly charred and chewy. Cacio e Pepe is also outstanding. A little noisy but that adds to the atmosphere.'),
    ('Bosphorus Seafood', 'hungry_traveller',
     5, 'Fine dining at its best. The sea bass was flawlessly cooked and the Bosphorus views are unbeatable. Yes it\'s expensive but for a special occasion it\'s absolutely perfect.'),
    ('Green Bowl', 'gourmet_explorer',
     5, 'Finally a vegetarian restaurant in Ankara that doesn\'t feel like an afterthought. The Buddha Bowl is hearty and delicious. Will be a regular haunt!'),
    ('Burger Republic', 'foodlover',
     4, 'Best burgers I\'ve had outside of the US. The smash patty technique gives an amazing crust. Price-to-quality ratio is exceptional.'),
    ('Ristorante La Dolce Vita', 'hungry_traveller',
     5, 'Impeccable in every way. The ossobuco is among the best I\'ve tasted outside of Milan. Wine list is exceptional. Worth every lira for a special evening.'),
]


class Command(BaseCommand):
    help = 'Seed the database with sample FlavorMap data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🗑️  Clearing existing data...')
            Review.objects.all().delete()
            MenuItem.objects.all().delete()
            OpeningHours.objects.all().delete()
            Restaurant.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        with transaction.atomic():
            self._create_categories()
            self._create_users()
            self._create_restaurants()
            self._create_reviews()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('  Accounts:')
        self.stdout.write('    🔑 admin       / admin123   (superuser)')
        self.stdout.write('    🏪 owner1      / owner123   (restaurant owner)')
        self.stdout.write('    👤 foodlover   / review123  (reviewer)')
        self.stdout.write('    👤 gourmet_explorer / review123')
        self.stdout.write('    👤 hungry_traveller / review123')
        self.stdout.write('')
        self.stdout.write('  Visit: http://127.0.0.1:8000')
        self.stdout.write('  Admin: http://127.0.0.1:8000/admin')

    def _create_categories(self):
        self.cats = {}
        for name, slug, icon in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon}
            )
            self.cats[slug] = cat
        self.stdout.write(f'  ✓ {len(self.cats)} categories')

    def _create_users(self):
        # Superuser / admin
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@flavormap.com', 'is_staff': True, 'is_superuser': True,
                      'first_name': 'Admin', 'last_name': 'FlavorMap'}
        )
        admin.set_password('admin123')
        admin.save()
        UserProfile.objects.get_or_create(user=admin, defaults={'is_owner': True})

        # Owner
        owner, _ = User.objects.get_or_create(
            username='owner1',
            defaults={'email': 'owner@flavormap.com', 'first_name': 'Mert', 'last_name': 'Kaya'}
        )
        owner.set_password('owner123')
        owner.save()
        UserProfile.objects.get_or_create(user=owner, defaults={'is_owner': True, 'location': 'Istanbul'})

        # Reviewers
        for uname, email, fname, lname in [
            ('foodlover',        'food@lover.com',      'Elif',   'Arslan'),
            ('gourmet_explorer', 'gourmet@explore.com', 'Selin',  'Demir'),
            ('hungry_traveller', 'hungry@travel.com',   'Kemal',  'Öztürk'),
        ]:
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={'email': email, 'first_name': fname, 'last_name': lname}
            )
            u.set_password('review123')
            u.save()
            UserProfile.objects.get_or_create(user=u, defaults={'bio': 'Food lover from Turkey'})

        self.stdout.write('  ✓ 5 users created')
        self.admin_user = admin
        self.owner_user = owner

    def _create_restaurants(self):
        owner = User.objects.get(username='owner1')
        for i, data in enumerate(RESTAURANTS):
            r, created = Restaurant.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'address':     data['address'],
                    'city':        data['city'],
                    'district':    data.get('district', ''),
                    'phone':       data.get('phone', ''),
                    'price_range': data['price_range'],
                    'category':    self.cats[data['category']],
                    'latitude':    data.get('lat'),
                    'longitude':   data.get('lng'),
                    'owner':       owner if i < 3 else None,
                    'is_claimed':  i < 3,
                }
            )
            if created:
                # Opening hours (Mon–Sat open, Sun closed)
                for day in range(7):
                    OpeningHours.objects.create(
                        restaurant=r, day=day,
                        open_time='12:00', close_time='23:00',
                        is_closed=(day == 6)
                    )
                # Menu items
                for name, desc, price, cat_slug in data['menu']:
                    MenuItem.objects.create(
                        restaurant=r, name=name, description=desc,
                        price=price, category=cat_slug
                    )
        self.stdout.write(f'  ✓ {len(RESTAURANTS)} restaurants + menus + opening hours')

    def _create_reviews(self):
        users = {u.username: u for u in User.objects.all()}
        count = 0
        for rest_name, username, rating, text in REVIEWS:
            try:
                restaurant = Restaurant.objects.get(name=rest_name)
                user = users.get(username)
                if not user:
                    continue
                rev, created = Review.objects.get_or_create(
                    restaurant=restaurant, user=user,
                    defaults={'rating': rating, 'text': text}
                )
                if created:
                    count += 1
                    # Owner reply to first review of each restaurant
                    if rev.restaurant.owner and not rev.replies.exists():
                        ReviewReply.objects.create(
                            review=rev,
                            user=rev.restaurant.owner,
                            text='Thank you so much for your kind words! We look forward to welcoming you back soon. 🙏'
                        )
                    # Add a like from admin
                    ReviewLike.objects.get_or_create(
                        review=rev,
                        user=User.objects.filter(is_superuser=True).first(),
                        defaults={'is_like': True}
                    )
            except Restaurant.DoesNotExist:
                pass

        # Add some favorites
        for uname in ['foodlover', 'gourmet_explorer']:
            try:
                u = User.objects.get(username=uname)
                for r in Restaurant.objects.all()[:3]:
                    Favorite.objects.get_or_create(user=u, restaurant=r)
            except User.DoesNotExist:
                pass

        self.stdout.write(f'  ✓ {count} reviews + replies + likes + favorites')