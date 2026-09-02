from django.test import TestCase
from django.urls import reverse
from app.models import User, UserRole, LandListing, ZoningType, Transaction, SavedListing


class CryptoLandBuyingTests(TestCase):
    def setUp(self):
        # Create Buyer
        self.buyer = User.objects.create_user(
            username='buyer1',
            email='buyer1@crypto.io',
            password='password123',
            role=UserRole.BUYER,
            first_name='Bob',
            last_name='Buyer',
            crypto_wallet_address='0xBuyer123456789'
        )

        # Create Seller
        self.seller = User.objects.create_user(
            username='seller1',
            email='seller1@crypto.io',
            password='password123',
            role=UserRole.SELLER,
            first_name='Sally',
            last_name='Seller',
            crypto_wallet_address='0xSeller987654321',
            is_verified_seller=True
        )

        # Create Admin
        self.admin = User.objects.create_superuser(
            username='admin1',
            email='admin@crypto.io',
            password='password123',
            role=UserRole.ADMIN,
            is_staff=True
        )

        # Create Land Listing
        self.land = LandListing.objects.create(
            title='Beachfront Paradise Parcel',
            description='Gorgeous 2-acre plot on white sand beach.',
            location='Malibu, California, USA',
            price_crypto=15.5,
            crypto_currency='ETH',
            price_usd=49600.00,
            size_sqm=8093.00,
            size_acres=2.00,
            zoning_type=ZoningType.RESIDENTIAL,
            parcel_id='CA-MAL-2026-9001',
            deed_verified=True,
            seller=self.seller,
            status=LandListing.Status.AVAILABLE
        )

    def test_land_list_view(self):
        response = self.client.get(reverse('app:land_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beachfront Paradise Parcel')
        self.assertContains(response, 'ETH')

    def test_land_detail_view(self):
        response = self.client.get(reverse('app:land_detail', kwargs={'slug': self.land.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beachfront Paradise Parcel')
        self.assertContains(response, 'Malibu, California, USA')

    def test_seller_create_land(self):
        self.client.login(username='seller1', password='password123')
        response = self.client.post(reverse('app:create_land'), {
            'title': 'Highland Ranch Plot',
            'description': '10-acre mountain parcel.',
            'state': 'Lagos',
            'lga': 'Eti Osa',
            'location': 'Lekki Phase 1',
            'price_crypto': '3.2',
            'crypto_currency': 'ETH',
            'price_usd': '10240.00',
            'size_sqm': '40468.00',
            'size_acres': '10.00',
            'zoning_type': ZoningType.RESIDENTIAL,
            'parcel_id': 'CO-DEN-2026-1122',
        })
        self.assertEqual(response.status_code, 302)
        created_land = LandListing.objects.get(parcel_id='CO-DEN-2026-1122')
        self.assertEqual(created_land.seller, self.seller)

    def test_buyer_submit_offer(self):
        self.client.login(username='buyer1', password='password123')
        response = self.client.post(reverse('app:submit_offer', kwargs={'slug': self.land.slug}), {
            'offer_price_crypto': '15.5',
            'crypto_currency': 'ETH',
            'offer_price_usd': '49600.00',
            'buyer_wallet_address': self.buyer.crypto_wallet_address,
            'notes': 'Ready to transfer to escrow immediately.',
        })
        self.assertEqual(response.status_code, 302)
        tx = Transaction.objects.filter(buyer=self.buyer, land=self.land).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.status, Transaction.Status.OFFER_SUBMITTED)

    def test_seller_accept_offer_and_buyer_payment(self):
        # Create offer
        tx = Transaction.objects.create(
            land=self.land,
            buyer=self.buyer,
            seller=self.seller,
            offer_price_crypto=15.5,
            crypto_currency='ETH',
            offer_price_usd=49600.00,
            buyer_wallet_address=self.buyer.crypto_wallet_address,
            status=Transaction.Status.OFFER_SUBMITTED
        )

        # Seller accepts
        self.client.login(username='seller1', password='password123')
        response = self.client.post(reverse('app:respond_to_offer', kwargs={'transaction_id': tx.transaction_id}), {
            'action': 'accept'
        })
        self.assertEqual(response.status_code, 302)
        tx.refresh_from_db()
        self.assertEqual(tx.status, Transaction.Status.ACCEPTED)

        # Buyer submits payment hash
        self.client.login(username='buyer1', password='password123')
        response = self.client.post(reverse('app:submit_payment_hash', kwargs={'transaction_id': tx.transaction_id}), {
            'tx_hash': '0xABCDEF1234567890ETHHASH'
        })
        self.assertEqual(response.status_code, 302)
        tx.refresh_from_db()
        self.assertEqual(tx.status, Transaction.Status.ESCROW_LOCKED)
        self.assertEqual(tx.tx_hash, '0xABCDEF1234567890ETHHASH')

    def test_admin_confirm_escrow_payment(self):
        tx = Transaction.objects.create(
            land=self.land,
            buyer=self.buyer,
            seller=self.seller,
            offer_price_crypto=15.5,
            crypto_currency='ETH',
            offer_price_usd=49600.00,
            buyer_wallet_address=self.buyer.crypto_wallet_address,
            tx_hash='0xABCDEF1234567890ETHHASH',
            status=Transaction.Status.ESCROW_LOCKED
        )

        self.client.login(username='admin1', password='password123')
        response = self.client.get(reverse('app:confirm_escrow_payment', kwargs={'transaction_id': tx.transaction_id}))
        self.assertEqual(response.status_code, 302)

        tx.refresh_from_db()
        self.land.refresh_from_db()
        self.assertEqual(tx.status, Transaction.Status.COMPLETED)
        self.assertEqual(self.land.status, LandListing.Status.SOLD)

    def test_user_registration_with_role_without_wallet(self):
        response = self.client.post(reverse('app:register'), {
            'username': 'newbuyer',
            'email': 'newbuyer@example.com',
            'first_name': 'New',
            'last_name': 'Buyer',
            'role': UserRole.BUYER,
            'password1': 'x9$K#mP2!vL7qW1z',
            'password2': 'x9$K#mP2!vL7qW1z',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='newbuyer')
        self.assertEqual(new_user.role, UserRole.BUYER)

    def test_lgas_api_endpoint(self):
        response = self.client.get(reverse('app:get_lgas_api') + '?state=Lagos')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['state'], 'Lagos')
        self.assertIn('Eti Osa', json_data['lgas'])
        self.assertIn('Ikeja', json_data['lgas'])
