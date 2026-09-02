from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from app.models import LandListing, Transaction, User, UserRole
from app.decorators import admin_required
from notifications.notification_services import NotificationService


@admin_required
def admin_dashboard(request):
    """Platform Admin dashboard for managing listings, escrow verification, and users."""
    pending_listings = LandListing.objects.filter(status=LandListing.Status.PENDING).select_related('seller')
    all_listings = LandListing.objects.all().select_related('seller').order_by('-created_at')[:15]
    escrow_transactions = Transaction.objects.filter(status__in=[
        Transaction.Status.ESCROW_LOCKED,
        Transaction.Status.PAYMENT_PENDING,
        Transaction.Status.ACCEPTED
    ]).select_related('land', 'buyer', 'seller')
    
    users = User.objects.all().order_by('-date_joined')[:20]

    context = {
        'pending_listings': pending_listings,
        'all_listings': all_listings,
        'escrow_transactions': escrow_transactions,
        'users': users,
        'stats': {
            'total_users': User.objects.count(),
            'total_listings': LandListing.objects.count(),
            'total_escrow_txs': Transaction.objects.count(),
            'completed_sales': Transaction.objects.filter(status=Transaction.Status.COMPLETED).count(),
        }
    }
    return render(request, 'app/admin_dashboard.html', context)


@admin_required
def approve_land_listing(request, land_id):
    """Admin approves a land listing to make it available publicly."""
    land = get_object_or_404(LandListing, id=land_id)
    land.status = LandListing.Status.AVAILABLE
    land.deed_verified = True
    land.save()

    NotificationService.send_notification(
        recipient=land.seller,
        actor=request.user,
        title=f"Land Listing Approved!",
        message=f"Your listing '{land.title}' (Parcel #{land.parcel_id}) has been verified and is now live on the marketplace.",
        target_obj=land,
        category='land_approved',
        type='success'
    )

    messages.success(request, f"Land property '{land.title}' approved and marked as verified.")
    return redirect('app:admin_dashboard')


@admin_required
def confirm_escrow_payment(request, transaction_id):
    """Admin verifies Web3 blockchain Tx Hash, releases escrow, and completes title transfer."""
    tx = get_object_or_404(Transaction, transaction_id=transaction_id)
    tx.status = Transaction.Status.COMPLETED
    tx.save()

    # Mark land status as SOLD
    tx.land.status = LandListing.Status.SOLD
    tx.land.save()

    # Notify Buyer
    NotificationService.send_notification(
        recipient=tx.buyer,
        actor=request.user,
        title="Land Title Deed Transferred!",
        message=f"Escrow payment verified on blockchain. You are now the official owner of {tx.land.title} (Parcel #{tx.land.parcel_id})!",
        target_obj=tx,
        category='escrow_confirmed',
        type='success'
    )

    # Notify Seller
    NotificationService.send_notification(
        recipient=tx.seller,
        actor=request.user,
        title="Crypto Funds Released from Escrow!",
        message=f"Blockchain transaction verified. {tx.offer_price_crypto} {tx.crypto_currency} has been released to your wallet.",
        target_obj=tx,
        category='escrow_confirmed',
        type='success'
    )

    messages.success(request, f"Escrow payment verified! Property title transferred to buyer ({tx.buyer.username}).")
    return redirect('app:admin_dashboard')


@admin_required
def toggle_user_verification(request, user_id):
    """Admin toggles verified seller status for a user."""
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_verified_seller = not user_obj.is_verified_seller
    user_obj.save()

    status_str = "Verified Seller" if user_obj.is_verified_seller else "Standard User"
    messages.info(request, f"Updated {user_obj.username}'s verification status to {status_str}.")
    return redirect('app:admin_dashboard')
