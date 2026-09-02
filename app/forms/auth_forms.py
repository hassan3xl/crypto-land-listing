from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from app.models import User, UserRole


class UserRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[(UserRole.BUYER, 'Land Buyer'), (UserRole.SELLER, 'Land Seller')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=UserRole.BUYER,
        help_text="Select whether you want to buy land or list land for sale"
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'name@example.com', 'class': 'form-control'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': '+1 (555) 000-0000', 'class': 'form-control'}))
    preferred_currency = forms.ChoiceField(
        choices=[('ETH', 'Ethereum (ETH)'), ('SOL', 'Solana (SOL)'), ('BTC', 'Bitcoin (BTC)'), ('USDT', 'Tether (USDT)')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='ETH',
        required=False
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'preferred_currency')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            username = username.strip()
            # If user provided an email address instead of username, resolve username
            if '@' in username or not User.objects.filter(username=username).exists():
                user_obj = User.objects.filter(email__iexact=username).first()
                if user_obj:
                    username = user_obj.username

            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
