from whitenoise.storage import CompressedManifestStaticFilesStorage


class LenientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Manifest storage that tolerates optional assets that are not present.

    The landing page references assets (logo, photos) that may not have been
    added yet. With the stock manifest storage, {% static %} raises ValueError
    for such a file when DEBUG is off, turning the whole page into an HTTP 500.
    Here it falls back to the plain, unhashed URL; the browser 404s only that
    one asset and the page hides the broken <img>.
    """

    manifest_strict = False

    def url(self, name, force=False):
        try:
            return super().url(name, force)
        except ValueError:
            return self._plain_url(name)

    def _plain_url(self, name):
        from django.contrib.staticfiles.storage import StaticFilesStorage

        return StaticFilesStorage.url(self, name)
