"""Localizer: translates UI strings into the user's base language.

Inject a Localizer instance via constructor; do not call t() directly.
"""

from bot.config.messages import CATALOGS, DEFAULT_LOCALE


class Localizer:
    def t(self, key: type, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
        """Resolve a UI string by key and locale, with English fallback."""
        catalog = CATALOGS.get(locale, CATALOGS[DEFAULT_LOCALE])
        template = catalog.get(key, CATALOGS[DEFAULT_LOCALE][key])
        return template.format(**kwargs) if kwargs else template
