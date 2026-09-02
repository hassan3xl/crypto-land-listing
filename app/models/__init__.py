import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone
from app.utils.exchange_rates import convert_crypto_to_usd


class UserRole(models.TextChoices):
    BUYER = 'buyer', 'Buyer'
    SELLER = 'seller', 'Seller'
    ADMIN = 'admin', 'Admin'


class ZoningType(models.TextChoices):
    RESIDENTIAL = 'residential', 'Residential'
    COMMERCIAL = 'commercial', 'Commercial'
    AGRICULTURAL = 'agricultural', 'Agricultural'
    INDUSTRIAL = 'industrial', 'Industrial'
    MIXED_USE = 'mixed_use', 'Mixed-Use'
    WATERFRONT = 'waterfront', 'Waterfront'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.BUYER)
    phone = models.CharField(max_length=24, blank=True)
    crypto_wallet_address = models.CharField(max_length=128, blank=True, help_text="Web3 Wallet Address (ETH, SOL, BTC, USDT)")
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_verified_seller = models.BooleanField(default=False)

    def is_buyer(self):
        return self.role == UserRole.BUYER

    def is_seller(self):
        return self.role == UserRole.SELLER or self.is_superuser

    def is_admin_user(self):
        return self.role == UserRole.ADMIN or self.is_superuser or self.is_staff

    def get_wallet_for_currency(self, currency):
        """Returns seller's default saved wallet address for a given currency, fallback to primary wallet address."""
        wallet = self.saved_wallets.filter(currency=currency, is_default=True).first()
        if not wallet:
            wallet = self.saved_wallets.filter(currency=currency).first()
        if wallet:
            return wallet.wallet_address
        return self.crypto_wallet_address or ''

    @property
    def get_avatar_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return None

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class SellerWallet(models.Model):
    class Currency(models.TextChoices):
        ETH = 'ETH', 'Ethereum (ETH)'
        SOL = 'SOL', 'Solana (SOL)'
        BTC = 'BTC', 'Bitcoin (BTC)'
        USDT = 'USDT', 'Tether (USDT)'
        BNB = 'BNB', 'BNB Smart Chain (BNB)'
        MATIC = 'MATIC', 'Polygon (MATIC)'
        OTHER = 'OTHER', 'Other Crypto'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_wallets')
    label = models.CharField(max_length=100, help_text="Wallet Label (e.g. Primary ETH Treasury, Solana Cold Storage, Business BTC)")
    currency = models.CharField(max_length=20, choices=Currency.choices, default=Currency.ETH)
    wallet_address = models.CharField(max_length=128)
    is_default = models.BooleanField(default=False, help_text="Set as default wallet for this currency")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        if not self.label or not self.label.strip():
            currency_names = {
                'ETH': 'Ethereum Wallet',
                'SOL': 'Solana Wallet',
                'BTC': 'Bitcoin Wallet',
                'USDT': 'USDT Wallet',
                'BNB': 'BNB Wallet',
                'MATIC': 'Polygon Wallet',
                'OTHER': 'Crypto Wallet',
            }
            self.label = currency_names.get(self.currency, f"{self.currency} Wallet")

        if self.is_default:
            SellerWallet.objects.filter(user=self.user, currency=self.currency).exclude(pk=self.pk).update(is_default=False)
            self.user.crypto_wallet_address = self.wallet_address
            self.user.save(update_fields=['crypto_wallet_address'])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} ({self.currency}) — {self.wallet_address[:10]}..."


class LandListing(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        AVAILABLE = 'available', 'Available'
        UNDER_CONTRACT = 'under_contract', 'Under Contract'
        SOLD = 'sold', 'Sold'
        REJECTED = 'rejected', 'Rejected'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255, help_text="City/Area, State, Country (e.g. Lekki Phase 1, Lagos State)")
    state = models.CharField(max_length=50, blank=True, help_text="State / FCT")
    lga = models.CharField(max_length=100, blank=True, help_text="Local Government Area (LGA)")
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    price_crypto = models.DecimalField(max_digits=18, decimal_places=6)
    crypto_currency = models.CharField(
        max_length=10,
        choices=[('ETH', 'ETH'), ('SOL', 'SOL'), ('BTC', 'BTC'), ('USDT', 'USDT')],
        default='ETH'
    )
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    size_sqm = models.DecimalField(max_digits=12, decimal_places=2, help_text="Land Area in Square Meters (Sqm)")
    size_acres = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Size in Acres/Hectares")
    zoning_type = models.CharField(max_length=50, choices=ZoningType.choices, default=ZoningType.RESIDENTIAL)
    
    parcel_id = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Title Document / Survey Plan No. (e.g. C of O No. 2026/8819)")
    deed_verified = models.BooleanField(default=True)
    featured_image = models.ImageField(upload_to='land_images/', blank=True, null=True)
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='land_listings')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def get_featured_image_url(self):
        """Return featured image URL, gallery first image URL, or standard land fallback."""
        if self.featured_image:
            try:
                return self.featured_image.url
            except Exception:
                pass
        first_gallery = self.images.first()
        if first_gallery and first_gallery.image:
            try:
                return first_gallery.image.url
            except Exception:
                pass
        return "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=800&q=80"

    @property
    def formatted_size_plots(self):
        """Format land size using Nigerian real estate metrics (Sqm & Plots / Hectares)."""
        sqm = float(self.size_sqm or 0)
        if sqm >= 10000:
            hectares = round(sqm / 10000, 2)
            return f"{sqm:,.0f} m² ({hectares} Ha)"
        elif sqm >= 450:
            plots = round(sqm / 600, 1)
            plots_str = f"{plots:g} Plot" if plots == 1 else f"{plots:g} Plots"
            return f"{sqm:,.0f} m² ({plots_str})"
        return f"{sqm:,.0f} m²"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'land'
            slug = base_slug
            counter = 1
            while LandListing.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.parcel_id:
            self.parcel_id = f"NG-SURVEY-{uuid.uuid4().hex[:8].upper()}"

        if self.price_crypto and (not self.price_usd or self.price_usd == 0):
            self.price_usd = convert_crypto_to_usd(self.price_crypto, self.crypto_currency)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.price_crypto} {self.crypto_currency}"


class LandImage(models.Model):
    land = models.ForeignKey(LandListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='land_gallery/')
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.land.title}"


class Transaction(models.Model):
    class Status(models.TextChoices):
        OFFER_SUBMITTED = 'offer_submitted', 'Offer Submitted'
        ACCEPTED = 'accepted', 'Offer Accepted'
        PAYMENT_PENDING = 'payment_pending', 'Payment Pending'
        ESCROW_LOCKED = 'escrow_locked', 'Escrow Locked (Verification)'
        COMPLETED = 'completed', 'Completed & Transferred'
        REJECTED = 'rejected', 'Offer Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    land = models.ForeignKey(LandListing, on_delete=models.CASCADE, related_name='transactions')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_transactions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_transactions')
    
    offer_price_crypto = models.DecimalField(max_digits=18, decimal_places=6)
    crypto_currency = models.CharField(max_length=10, default='ETH')
    offer_price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    
    buyer_wallet_address = models.CharField(max_length=128)
    seller_wallet_address = models.CharField(max_length=128, blank=True)
    escrow_wallet_address = models.CharField(max_length=128, blank=True, default='0x71C7656EC7ab88b098defB751B7401B5f6d8976F')
    tx_hash = models.CharField(max_length=128, blank=True, null=True, help_text="Blockchain Tx Hash")
    
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OFFER_SUBMITTED)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.offer_price_crypto and (not self.offer_price_usd or self.offer_price_usd == 0):
            self.offer_price_usd = convert_crypto_to_usd(self.offer_price_crypto, self.crypto_currency)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Tx {str(self.transaction_id)[:8]} - {self.land.title} ({self.status})"


class SavedListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_lands')
    land = models.ForeignKey(LandListing, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'land')

    def __str__(self):
        return f"{self.user.username} saved {self.land.title}"
