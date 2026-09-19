class OslabError(RuntimeError):
    """An expected installation or verification error."""


class ManifestError(OslabError):
    """The checked-in environment definition is incomplete or invalid."""


class VerificationError(OslabError):
    """An installed component does not meet the expected contract."""
