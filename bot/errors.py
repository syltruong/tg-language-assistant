"""Domain error types.

Shared leaf module — no imports from other bot modules. Both the module that
raises an error and the Localizer that renders it import from here.
"""


class UserFacingError(Exception):
    def __init__(self, *args, **format_kwargs):
        super().__init__(*args)
        self.format_kwargs = format_kwargs


class MessageHasNoTextError(UserFacingError):
    pass


class TextHasNoWrittenContentError(UserFacingError):
    pass


class TextTooLongError(UserFacingError):
    pass


class UnauthorizedError(UserFacingError):
    pass


class UnsupportedLanguage(UserFacingError):
    """Raised when the detected language is neither the user's base nor target language."""
    pass
