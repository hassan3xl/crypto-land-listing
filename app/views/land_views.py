from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from app.models import LandListing, Transaction, SavedListing, UserRole, ZoningType, LandImage
from app.forms.land_forms import LandListingForm, LandFilterForm, SubmitOfferForm, CryptoPaymentTxForm
from app.decorators import seller_required, buyer_required
from notifications.notification_services import NotificationService


from app.utils import get_lgas_for_state, NIGERIA_STATES_AND_LGAS, get_all_rates_dict, convert_crypto_to_usd


def get_lgas_api(request):
    """API endpoint returning LGAs for a requested state in JSON."""
    state = request.GET.get('state', '').strip()
    lgas = get_lgas_for_state(state)
    return JsonResponse({'state': state, 'lgas': lgas})


def get_exchange_rates_api(request):
    """API endpoint returning current crypto exchange rates and calculated values."""
    rates = get_all_rates_dict()
    amount = request.GET.get('amount')
    currency = request.GET.get('currency', 'ETH').upper()
    
    usd_val = None
    if amount:
        usd_val = float(convert_crypto_to_usd(amount, currency))
        
    return JsonResponse({
        'rates': rates,
        'requested_amount': amount,
        'requested_currency': currency,
        'calculated_usd': usd_val
    })


def land_list(request):
    """Filterable, searchable catalogue of available land listings."""
    form = LandFilterForm(request.GET)
    queryset = LandListing.objects.filter(status=LandListing.Status.AVAILABLE)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q) |
                Q(state__icontains=q) |
                Q(lga__icontains=q) |
                Q(parcel_id__icontains=q)
            )

        state = form.cleaned_data.get('state')
        if state:
            queryset = queryset.filter(state__iexact=state)

        lga = form.cleaned_data.get('lga')
        if lga:
            queryset = queryset.filter(lga__iexact=lga)
        
        zoning = form.cleaned_data.get('zoning')
        if zoning:
            queryset = queryset.filter(zoning_type=zoning)
            
        crypto_curr = form.cleaned_data.get('crypto_currency')
        if crypto_curr:
            queryset = queryset.filter(crypto_currency=crypto_curr)
            
        min_price = form.cleaned_data.get('min_price')
        if min_price:
            queryset = queryset.filter(price_usd__gte=min_price)
            
        max_price = form.cleaned_data.get('max_price')
        if max_price:
            queryset = queryset.filter(price_usd__lte=max_price)
            
        min_size = form.cleaned_data.get('min_size')
        if min_size:
            queryset = queryset.filter(size_sqm__gte=min_size)
            
        sort = form.cleaned_data.get('sort')
        if sort:
            queryset = queryset.order_by(sort)
        else:
            queryset = queryset.order_by('-created_at')

    # Get saved land IDs for authenticated user
    saved_land_ids = []
    if request.user.is_authenticated:
        saved_land_ids = list(SavedListing.objects.filter(user=request.user).values_list('land_id', flat=True))

    context = {
        'lands': queryset,
        'filter_form': form,
        'saved_land_ids': saved_land_ids,
        'results_count': queryset.count(),
    }
    return render(request, 'app/land_list.html', context)


def land_detail(request, slug):
    """Detailed view for a single land listing including specs, seller info, and offer modal."""
    land = get_object_or_404(LandListing, slug=slug)
    
    # Increment view count
    land.views_count += 1
    land.save(update_fields=['views_count'])

    is_saved = False
    existing_offer = None
    if request.user.is_authenticated:
        is_saved = SavedListing.objects.filter(user=request.user, land=land).exists()
        if request.user.is_buyer():
            existing_offer = Transaction.objects.filter(buyer=request.user, land=land).order_by('-created_at').first()

    offer_form = SubmitOfferForm(initial={
        'offer_price_crypto': land.price_crypto,
        'crypto_currency': land.crypto_currency,
        'offer_price_usd': land.price_usd,
        'buyer_wallet_address': request.user.crypto_wallet_address if request.user.is_authenticated else '',
    })

    payment_form = CryptoPaymentTxForm()

    context = {
        'land': land,
        'is_saved': is_saved,
        'existing_offer': existing_offer,
        'offer_form': offer_form,
        'payment_form': payment_form,
    }
    return render(request, 'app/land_detail.html', context)


@seller_required
def create_land(request):
    """Seller view to create and list new land property."""
    if request.method == 'POST':
        form = LandListingForm(request.POST, request.FILES)
        if form.is_valid():
            land = form.save(commit=False)
            land.seller = request.user
            # Auto-approve if verified seller or superuser, else pending
            if request.user.is_verified_seller or request.user.is_superuser:
                land.status = LandListing.Status.AVAILABLE
            else:
                land.status = LandListing.Status.AVAILABLE # default available for fast testing
            land.save()

            messages.success(request, f"Land property '{land.title}' created and listed successfully!")
            return redirect('app:land_detail', slug=land.slug)
        else:
            messages.error(request, "Failed to list property. Please check form errors below.")
    else:
        form = LandListingForm(initial={
            'crypto_currency': request.user.preferred_currency or 'ETH',
            'latitude': 30.2672,
            'longitude': -97.7431
        })

    return render(request, 'app/create_land.html', {'form': form, 'title': 'List New Land Property'})


@seller_required
def edit_land(request, slug):
    """Seller view to update an existing land listing."""
    land = get_object_or_404(LandListing, slug=slug)
    if land.seller != request.user and not request.user.is_superuser:
        messages.error(request, "You are not authorized to edit this property.")
        return redirect('app:land_detail', slug=slug)

    if request.method == 'POST':
        form = LandListingForm(request.POST, request.FILES, instance=land)
        if form.is_valid():
            form.save()
            messages.success(request, f"Property '{land.title}' updated successfully!")
            return redirect('app:land_detail', slug=land.slug)
    else:
        form = LandListingForm(instance=land)

    return render(request, 'app/create_land.html', {'form': form, 'land': land, 'is_edit': True, 'title': f'Edit {land.title}'})


@seller_required
def delete_land(request, slug):
    """Seller view to remove land listing."""
    land = get_object_or_404(LandListing, slug=slug)
    if land.seller != request.user and not request.user.is_superuser:
        messages.error(request, "Not authorized.")
        return redirect('app:seller_dashboard')

    if request.method == 'POST':
        land.delete()
        messages.success(request, "Land property listing removed.")
        return redirect('app:seller_dashboard')

    return render(request, 'app/confirm_delete.html', {'object': land, 'type': 'Land Property'})


@buyer_required
def submit_offer(request, slug):
    """Buyer initiates a purchase offer on a land listing."""
    land = get_object_or_404(LandListing, slug=slug)
    if request.method == 'POST':
        form = SubmitOfferForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.land = land
            tx.buyer = request.user
            tx.seller = land.seller
            tx.seller_wallet_address = land.seller.crypto_wallet_address or '0xSellerWalletPendingVerification'
            tx.status = Transaction.Status.OFFER_SUBMITTED
            tx.save()

            # Send Notification to Seller
            NotificationService.send_notification(
                recipient=land.seller,
                actor=request.user,
                title=f"New Crypto Offer on {land.title}",
                message=f"{request.user.first_name or request.user.username} offered {tx.offer_price_crypto} {tx.crypto_currency} (~${tx.offer_price_usd:,.2f}) for your land.",
                target_obj=tx,
                category='offer_received',
                type='info'
            )

            messages.success(request, f"Crypto purchase offer for {tx.offer_price_crypto} {tx.crypto_currency} submitted to the seller!")
            return redirect('app:buyer_dashboard')
        else:
            messages.error(request, "Failed to submit offer. Check input values.")
    return redirect('app:land_detail', slug=slug)


@login_required
def respond_to_offer(request, transaction_id):
    """Seller accepts or rejects a buyer's offer."""
    tx = get_object_or_404(Transaction, transaction_id=transaction_id)
    if tx.seller != request.user and not request.user.is_superuser:
        messages.error(request, "Not authorized.")
        return redirect('app:seller_dashboard')

    action = request.POST.get('action')
    if action == 'accept':
        tx.status = Transaction.Status.ACCEPTED
        tx.land.status = LandListing.Status.UNDER_CONTRACT
        tx.land.save()
        tx.save()

        NotificationService.send_notification(
            recipient=tx.buyer,
            actor=request.user,
            title=f"Offer Accepted for {tx.land.title}!",
            message=f"Seller accepted your offer of {tx.offer_price_crypto} {tx.crypto_currency}. Please complete your Web3 crypto payment to escrow.",
            target_obj=tx,
            category='offer_accepted',
            type='success'
        )
        messages.success(request, f"Offer accepted! Property status updated to Under Contract. Awaiting buyer's Web3 crypto payment.")
    elif action == 'reject':
        tx.status = Transaction.Status.REJECTED
        tx.save()
        NotificationService.send_notification(
            recipient=tx.buyer,
            actor=request.user,
            title=f"Offer Response for {tx.land.title}",
            message=f"Seller declined your purchase offer.",
            target_obj=tx,
            category='offer_received',
            type='warning'
        )
        messages.info(request, "Offer declined.")

    return redirect('app:seller_dashboard')


@buyer_required
def submit_payment_hash(request, transaction_id):
    """Buyer submits Web3 blockchain transaction hash after transferring funds to Escrow."""
    tx = get_object_or_404(Transaction, transaction_id=transaction_id, buyer=request.user)
    if request.method == 'POST':
        form = CryptoPaymentTxForm(request.POST, instance=tx)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.status = Transaction.Status.ESCROW_LOCKED
            transaction.save()

            NotificationService.send_notification(
                recipient=tx.seller,
                actor=request.user,
                title=f"Crypto Payment Escrowed for {tx.land.title}",
                message=f"Buyer submitted transaction hash: {transaction.tx_hash[:12]}... Awaiting Admin escrow verification.",
                target_obj=tx,
                category='payment_submitted',
                type='success'
            )

            messages.success(request, "Tx Hash submitted! Payment is locked in Escrow. Admin & Seller are reviewing block verification.")
            return redirect('app:buyer_dashboard')

    return redirect('app:buyer_dashboard')


@login_required
def toggle_save_land(request, land_id):
    """Bookmark / save land listing toggle endpoint."""
    land = get_object_or_404(LandListing, id=land_id)
    saved_item, created = SavedListing.objects.get_or_create(user=request.user, land=land)
    
    if not created:
        saved_item.delete()
        is_saved = False
        msg = "Removed from saved lands."
    else:
        is_saved = True
        msg = "Saved to your favorites!"

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': is_saved, 'message': msg})

    messages.info(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'app:land_list'))


@buyer_required
def buyer_dashboard(request):
    """Buyer dashboard showing saved properties, active purchase contracts, and history."""
    saved_lands = SavedListing.objects.filter(user=request.user).select_related('land')
    my_offers = Transaction.objects.filter(buyer=request.user).select_related('land', 'seller')
    
    context = {
        'saved_lands': saved_lands,
        'my_offers': my_offers,
        'payment_form': CryptoPaymentTxForm(),
    }
    return render(request, 'app/buyer_dashboard.html', context)


@seller_required
def seller_dashboard(request):
    """Seller dashboard displaying listed lands, received offers, and revenue stats."""
    my_listings = LandListing.objects.filter(seller=request.user)
    received_offers = Transaction.objects.filter(seller=request.user).select_related('land', 'buyer')
    
    # Revenue stats
    total_sales_crypto = Transaction.objects.filter(seller=request.user, status=Transaction.Status.COMPLETED)
    
    context = {
        'my_listings': my_listings,
        'received_offers': received_offers,
        'active_listings_count': my_listings.filter(status=LandListing.Status.AVAILABLE).count(),
        'under_contract_count': my_listings.filter(status=LandListing.Status.UNDER_CONTRACT).count(),
        'sold_count': my_listings.filter(status=LandListing.Status.SOLD).count(),
    }
    return render(request, 'app/seller_dashboard.html', context)
