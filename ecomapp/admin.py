from django.contrib import admin
from .models import (
    Products, Order, Cart, OrderItem, Category, SubCategory, 
    Coupon, CouponUsage, Address
)

# Inline SubCategory within Category Admin
class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1

# Category Admin with inline SubCategory
class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubCategoryInline]
    list_display = ['name', 'created_at']
    search_fields = ['name']

# Coupon Admin for better management
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_until', 'is_active', 'times_used']
    list_filter = ['is_active', 'discount_type']
    search_fields = ['code']
    readonly_fields = ['times_used']  # Prevent manual modification of usage count

# Coupon Usage Admin
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'used_at', 'order']
    list_filter = ['used_at']
    search_fields = ['coupon__code', 'user__username']

# Product Admin with bulk actions
@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['productname', 'price', 'is_active', 'category', 'createdAt']
    list_filter = ['is_active', 'category', 'subcategory']
    search_fields = ['productname', 'productinfo']
    actions = ['make_active', 'make_inactive']

    @admin.action(description="Mark selected products as active")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected products as inactive")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

# Register remaining models
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(OrderItem)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(CouponUsage, CouponUsageAdmin)
admin.site.register(Address)
