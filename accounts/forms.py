from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.db.models import Q


class BootstrapMixin:
    """Add Bootstrap classes so fields and errors are visible on every screen size."""

    @staticmethod
    def _base_class(widget):
        return "form-select" if isinstance(widget, forms.Select) else "form-control"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", self._base_class(field.widget))

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs["class"] = f"{self._base_class(widget)} is-invalid"


def normalize_email(value):
    return value.strip().lower()


class LoginForm(BootstrapMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Please enter a correct email and password. The password is case-sensitive.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update({"autocomplete": "email", "inputmode": "email"})

    def clean(self):
        # Accounts are stored with a lower-case email as the username, so "Member@Example.com " still logs in.
        username = self.cleaned_data.get("username")
        if username and "@" in username:
            self.cleaned_data["username"] = normalize_email(username)
        return super().clean()


class SignupForm(BootstrapMixin, BaseUserCreationForm):
    """Sign up with an email address and password. The email (lower case) is also the username."""

    email = forms.EmailField(
        label="Email",
        max_length=150,  # it is stored as the username, which allows 150 characters
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )

    class Meta(BaseUserCreationForm.Meta):
        model = get_user_model()
        fields = ("email",)
        field_classes = {}

    def clean_email(self):
        email = normalize_email(self.cleaned_data["email"])
        users = get_user_model().objects
        if users.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            raise forms.ValidationError("An account with this email already exists. Try logging in.")
        self.instance.username = email
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
