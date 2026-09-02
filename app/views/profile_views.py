from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.forms.profile_forms import UserProfileUpdateForm


@login_required
def profile_view(request):
    """View and update current user's profile details & Web3 Wallet."""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile & Crypto Wallet details updated successfully!")
            return redirect('app:profile')
        else:
            messages.error(request, "Failed to update profile. Please check form errors.")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'app/profile_edit.html', {'form': form})
