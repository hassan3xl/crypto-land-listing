from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from app.models import User, LandListing, LandImage, Transaction, SavedListing


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Crypto & Role Info', {'fields': ('role', 'phone', 'crypto_wallet_address', 'preferred_currency', 'profile_picture', 'bio', 'is_verified_seller')}),
    )
    list_display = ('username', 'email', 'role', 'is_verified_seller', 'crypto_wallet_address', 'is_staff')
    list_filter = ('role', 'is_verified_seller', 'is_staff', 'is_active')


class LandImageInline(admin.TabularInline):
    model = LandImage
    extra = 1


@admin.register(LandListing)
class LandListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'zoning_type', 'price_crypto', 'crypto_currency', 'price_usd', 'parcel_id', 'status', 'deed_verified', 'is_featured', 'created_at')
    list_filter = ('status', 'zoning_type', 'crypto_currency', 'deed_verified', 'is_featured')
    search_fields = ('title', 'location', 'parcel_id', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LandImageInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'land', 'buyer', 'seller', 'offer_price_crypto', 'crypto_currency', 'status', 'created_at')
    list_filter = ('status', 'crypto_currency')
    search_fields = ('transaction_id', 'land__title', 'buyer__username', 'seller__username', 'tx_hash')


@admin.register(SavedListing)
class SavedListingAdmin(admin.ModelAdmin):
    list_display = ('user', 'land', 'created_at')
