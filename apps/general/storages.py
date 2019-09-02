from contextlib import suppress

from storages.backends.s3boto import S3BotoStorage, safe_join as s3_safe_join


class AbsoluteAndS3BotoStorage(S3BotoStorage):
    def _normalize_name(self, name):
        with suppress(ValueError):
            return s3_safe_join(self.location, name)
