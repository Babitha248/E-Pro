from django.core.management.base import BaseCommand
from ecomapp.models import Category, SubCategory, Products
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates test data for the application'

    def handle(self, *args, **kwargs):
        # Create test user if not exists
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        if created:
            user.set_password('admin123')
            user.save()

        # Create test category
        category, _ = Category.objects.get_or_create(
            name='Electronics',
            defaults={'description': 'Electronic items'}
        )

        # Create test subcategory
        subcategory, _ = SubCategory.objects.get_or_create(
            name='Smartphones',
            category=category,
            defaults={'description': 'Mobile phones'}
        )

        # Create test product
        product, _ = Products.objects.get_or_create(
            productname='Test Phone',
            defaults={
                'user': user,
                'productbrand': 'Test Brand',
                'category': category,
                'subcategory': subcategory,
                'productinfo': 'Test product description',
                'price': 999.99,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully created test data')) 