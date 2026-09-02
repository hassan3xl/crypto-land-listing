from django import forms
from app.models import User, SellerWallet


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class SellerWalletForm(forms.ModelForm):
    label = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ethereum Wallet, Solana Wallet (Optional)'})
    )

    class Meta:
        model = SellerWallet
        fields = ['currency', 'wallet_address', 'label', 'is_default']
        widgets = {
            'currency': forms.Select(attrs={'class': 'form-select', 'id': 'id_wallet_currency'}),
            'wallet_address': forms.TextInput(attrs={'class': 'form-control font-monospace', 'placeholder': '0x... or Solana/BTC address'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
