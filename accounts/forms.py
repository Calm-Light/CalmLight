from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class BootstrapMixin:
    """Add Bootstrap classes so fields and errors are visible on every screen size."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs["class"] = "form-control is-invalid"


class LoginForm(BootstrapMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username or email"


class SignupForm(BootstrapMixin, UserCreationForm):
    pass
