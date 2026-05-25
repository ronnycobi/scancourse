"""
Tighter password rules than Django's defaults — must contain at least one
letter AND one digit. Length / common-word / numeric-only / similar-to-user
are still handled by Django's built-in validators upstream.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class LetterDigitValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise ValidationError(
                _('Password must contain at least one letter and one number.'),
                code='password_too_simple',
            )

    def get_help_text(self):
        return _('Your password must contain at least one letter and one number.')
