from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.forms.profile_forms import UserProfileUpdateForm, SellerWalletForm
from app.models import SellerWallet


@login_required
def profile_view(request):
    """View and update current user's profile details & manage saved Web3 Wallets."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_wallet':
            wallet_form = SellerWalletForm(request.POST)
            if wallet_form.is_valid():
                wallet = wallet_form.save(commit=False)
                wallet.user = request.user
                wallet.save()
                messages.success(request, f"Saved new crypto wallet '{wallet.label}' ({wallet.currency})!")
                return redirect('app:profile')
            else:
                messages.error(request, "Failed to add crypto wallet. Please check input values.")

        elif action == 'delete_wallet':
            wallet_id = request.POST.get('wallet_id')
            wallet = get_object_or_404(SellerWallet, pk=wallet_id, user=request.user)
            wallet.delete()
            messages.info(request, "Crypto wallet address deleted.")
            return redirect('app:profile')

        elif action == 'set_default_wallet':
            wallet_id = request.POST.get('wallet_id')
            wallet = get_object_or_404(SellerWallet, pk=wallet_id, user=request.user)
            wallet.is_default = True
            wallet.save()
            messages.success(request, f"Set '{wallet.label}' as default wallet for {wallet.currency}!")
            return redirect('app:profile')

        else:
            profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile details updated successfully!")
                return redirect('app:profile')
            else:
                messages.error(request, "Failed to update profile. Please check form errors.")

    profile_form = UserProfileUpdateForm(instance=request.user)
    wallet_form = SellerWalletForm()
    saved_wallets = request.user.saved_wallets.all()

    context = {
        'form': profile_form,
        'wallet_form': wallet_form,
        'saved_wallets': saved_wallets,
    }
    return render(request, 'app/profile_edit.html', context)
