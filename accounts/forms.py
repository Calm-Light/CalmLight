from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


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


class LoginForm(BootstrapMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username or email"


class SignupForm(BootstrapMixin, UserCreationForm):
    pass
