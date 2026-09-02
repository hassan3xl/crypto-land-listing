import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')
django.setup()

from app.models import User, UserRole, LandListing, ZoningType, Transaction, SavedListing, SellerWallet
from notifications.models.notification import Notification

def seed():
    print("Seeding MyApp database with Nigerian land plots & demo users...")

    # Create Admin User
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@MyApp.io',
            'first_name': 'Platform',
            'last_name': 'Administrator',
            'role': UserRole.ADMIN,
            'is_staff': True,
            'is_superuser': True,
            'crypto_wallet_address': '0x71C7656EC7ab88b098defB751B7401B5f6d8976F',
            'is_verified_seller': True
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print("-> Created admin user (admin / admin123)")

    # Create Seller 1
    seller1, created = User.objects.get_or_create(
        username='cryptoland_realty',
        defaults={
            'email': 'sales@cryptolandrealty.com',
            'first_name': 'Marcus',
            'last_name': 'Vance',
            'role': UserRole.SELLER,
            'phone': '+234 803 112 4490',
            'crypto_wallet_address': '0x9928A401c107B8821948b814FA7910028a192831',
            'is_verified_seller': True,
            'bio': 'Pioneer in crypto real estate and prime coastal land acquisitions across Lagos and Abuja.'
        }
    )
    if created:
        seller1.set_password('seller123')
        seller1.save()
        print("-> Created seller user (cryptoland_realty / seller123)")

    # Seed wallets for seller1
    SellerWallet.objects.get_or_create(
        user=seller1,
        currency='ETH',
        wallet_address='0x9928A401c107B8821948b814FA7910028a192831',
        defaults={'label': 'Ethereum Wallet', 'is_default': True}
    )
    SellerWallet.objects.get_or_create(
        user=seller1,
        currency='USDT',
        wallet_address='0x71C7656EC7ab88b098defB751B7401B5f6d8976F',
        defaults={'label': 'USDT Wallet', 'is_default': True}
    )
    SellerWallet.objects.get_or_create(
        user=seller1,
        currency='BTC',
        wallet_address='bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
        defaults={'label': 'Bitcoin Wallet', 'is_default': True}
    )

    # Create Seller 2
    seller2, created = User.objects.get_or_create(
        username='solana_acres',
        defaults={
            'email': 'contact@solanaacres.io',
            'first_name': 'Elena',
            'last_name': 'Rostova',
            'role': UserRole.SELLER,
            'phone': '+234 812 400 9911',
            'crypto_wallet_address': '8zF49bHqW8mKLn201PqxT9A1ZLm472NkaP83mV',
            'is_verified_seller': True,
            'bio': 'Specializing in commercial zoning plots and agricultural hectares in Lagos, Abuja, and Port Harcourt.'
        }
    )
    if created:
        seller2.set_password('seller123')
        seller2.save()
        print("-> Created seller user (solana_acres / seller123)")

    # Seed wallets for seller2
    SellerWallet.objects.get_or_create(
        user=seller2,
        currency='SOL',
        wallet_address='8zF49bHqW8mKLn201PqxT9A1ZLm472NkaP83mV',
        defaults={'label': 'Solana Wallet', 'is_default': True}
    )
    SellerWallet.objects.get_or_create(
        user=seller2,
        currency='ETH',
        wallet_address='0x5B38Da6a701c568545dCfcB03FcB875f56beddC4',
        defaults={'label': 'Ethereum Wallet', 'is_default': True}
    )

    # Create Buyer
    buyer1, created = User.objects.get_or_create(
        username='alex_investor',
        defaults={
            'email': 'alex@web3investor.com',
            'first_name': 'Alex',
            'last_name': 'Chen',
            'role': UserRole.BUYER,
            'phone': '+234 809 555 1200',
            'crypto_wallet_address': '0x438A9114b09C38194A1029F8a00293a81038101',
            'bio': 'Web3 investor acquiring physical land assets for long-term vault holding.'
        }
    )
    if created:
        buyer1.set_password('buyer123')
        buyer1.save()
        print("-> Created buyer user (alex_investor / buyer123)")

    # Sample Nigerian Land Properties
    lands_data = [
        {
            'title': '2 Plots of Prime Residential Land in Lekki Phase 1',
            'description': 'Dry, fully fenced 2-plot parcel in a secure gated neighborhood off Freedom Way, Lekki Phase 1. Perfect for luxury residential duplexes. Clear title deed with Certificate of Occupancy (C of O) and approved survey plan.',
            'state': 'Lagos',
            'lga': 'Eti Osa',
            'location': 'Lekki Phase 1',
            'address': 'Off Freedom Way, Lekki Phase 1, Lagos State',
            'latitude': 6.4549,
            'longitude': 3.4246,
            'price_crypto': 28.5,
            'crypto_currency': 'ETH',
            'price_usd': 91200.00,
            'size_sqm': 1200.00,
            'size_acres': 0.30,
            'zoning_type': ZoningType.RESIDENTIAL,
            'parcel_id': 'C of O No. LA/2026/8819',
            'deed_verified': True,
            'seller': seller1,
            'is_featured': True,
            'status': LandListing.Status.AVAILABLE,
        },
        {
            'title': 'Commercial Corner Plot in Maitama Extension',
            'description': 'Prime commercial corner plot in Maitama Extension, Abuja. High-density commercial zoning allowance for mixed office and retail development. Dual access road frontage.',
            'state': 'FCT Abuja',
            'lga': 'Abuja Municipal Area Council (AMAC)',
            'location': 'Maitama Extension',
            'address': 'Plot 402, Maitama Extension, Abuja FCT',
            'latitude': 9.0765,
            'longitude': 7.3986,
            'price_crypto': 1420.00,
            'crypto_currency': 'SOL',
            'price_usd': 205900.00,
            'size_sqm': 1800.00,
            'size_acres': 0.45,
            'zoning_type': ZoningType.COMMERCIAL,
            'parcel_id': 'C of O No. FCT/2026/0042',
            'deed_verified': True,
            'seller': seller2,
            'is_featured': True,
            'status': LandListing.Status.AVAILABLE,
        },
        {
            'title': '5-Hectare Agricultural Agro-Investment Land',
            'description': 'Fertile agricultural land in Epe along the expansion corridor. Ideal for commercial farming, greenhouse cultivation, or long-term land banking. Government Gazette title.',
            'state': 'Lagos',
            'lga': 'Epe',
            'location': 'Itoikin Road, Epe',
            'address': 'Itoikin Road, Epe, Lagos State',
            'latitude': 6.5841,
            'longitude': 3.9833,
            'price_crypto': 2.15,
            'crypto_currency': 'BTC',
            'price_usd': 137600.00,
            'size_sqm': 50000.00,
            'size_acres': 12.35,
            'zoning_type': ZoningType.AGRICULTURAL,
            'parcel_id': 'Gazette No. EP/2026/5510',
            'deed_verified': True,
            'seller': seller1,
            'is_featured': True,
            'status': LandListing.Status.AVAILABLE,
        },
        {
            'title': 'Waterfront Resort & Beachfront Plot in Ibeju-Lekki',
            'description': 'Pristine beachfront parcel with white sand coastline and lagoon access in Ibeju-Lekki. Ideal for eco-resort, beach club, or private estate. Excision approved title document.',
            'state': 'Lagos',
            'lga': 'Ibeju-Lekki',
            'location': 'Coastal Road Corridor',
            'address': 'Coastal Road Corridor, Ibeju-Lekki, Lagos State',
            'latitude': 6.4281,
            'longitude': 3.8211,
            'price_crypto': 150000.00,
            'crypto_currency': 'USDT',
            'price_usd': 150000.00,
            'size_sqm': 2400.00,
            'size_acres': 0.60,
            'zoning_type': ZoningType.WATERFRONT,
            'parcel_id': 'Excision Ref # IBL/2026/9921',
            'deed_verified': True,
            'seller': seller2,
            'is_featured': True,
            'status': LandListing.Status.AVAILABLE,
        },
        {
            'title': 'Industrial Logistics & Warehousing Plot',
            'description': 'Flat industrial-zoned parcel directly accessible from Trans-Amadi Expressway. High voltage grid connection and perimeter drainage established.',
            'state': 'Rivers',
            'lga': 'Port Harcourt',
            'location': 'Trans-Amadi Industrial Layout',
            'address': 'Trans-Amadi Industrial Layout, Port Harcourt, Rivers State',
            'latitude': 4.8156,
            'longitude': 7.0498,
            'price_crypto': 45.00,
            'crypto_currency': 'ETH',
            'price_usd': 144000.00,
            'size_sqm': 10000.00,
            'size_acres': 2.47,
            'zoning_type': ZoningType.INDUSTRIAL,
            'parcel_id': 'C of O No. RV/2026/1109',
            'deed_verified': True,
            'seller': seller1,
            'is_featured': False,
            'status': LandListing.Status.AVAILABLE,
        }
    ]

    for item in lands_data:
        land, created_land = LandListing.objects.update_or_create(
            parcel_id=item['parcel_id'],
            defaults=item
        )
        print(f"-> Seeded Land: {land.title} in {land.state} ({land.lga})")

    # Sample Purchase Offer
    sample_land = LandListing.objects.filter(parcel_id='C of O No. LA/2026/8819').first()
    if sample_land and buyer1:
        tx, created_tx = Transaction.objects.get_or_create(
            land=sample_land,
            buyer=buyer1,
            seller=sample_land.seller,
            defaults={
                'offer_price_crypto': 28.5,
                'crypto_currency': 'ETH',
                'offer_price_usd': 91200.00,
                'buyer_wallet_address': buyer1.crypto_wallet_address,
                'seller_wallet_address': sample_land.seller.crypto_wallet_address,
                'status': Transaction.Status.OFFER_SUBMITTED,
                'notes': 'Submitting binding offer with immediate Web3 escrow fund availability.'
            }
        )
        if created_tx:
            print("-> Created sample buyer purchase offer!")

        # Create sample notifications
        Notification.objects.get_or_create(
            recipient=sample_land.seller,
            actor=buyer1,
            title=f"New Crypto Offer on {sample_land.title}",
            defaults={
                'message': f"{buyer1.first_name or buyer1.username} offered 28.5 ETH (~$91,200.00) for your land in Lekki Phase 1.",
                'category': 'offer_received',
                'type': 'info'
            }
        )

        Notification.objects.get_or_create(
            recipient=buyer1,
            actor=admin,
            title="Welcome to MyApp Crypto Land Marketplace",
            defaults={
                'message': "Your account is active. You can browse verified land plots, submit Web3 crypto offers, and lock funds in escrow.",
                'category': 'system_alert',
                'type': 'success'
            }
        )

    print("Seeding completed successfully!")

if __name__ == '__main__':
    seed()
