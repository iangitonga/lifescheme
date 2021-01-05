import base64
from django.core import signing


class SigningError(Exception):
    """Raised when a value cannot be signed or unsigned."""
    pass


class Signer:
    """A class for providing signing and unsigning services.

    This class allows signing strings only.
    Notes:
        Methods of this class try to sign or unsign a given value and if an
        exception is raised, it is caught and `SigningError` is raised. This
        has been done deliberately to provide consistency to the caller of the
        method. This is caused by the fact that signing implementation by
        Django does not provide guarantees on exceptions raised and thus
        relying on them is not a choice.
    """
    def sign(self, value):
        """Creates a signed and timestamped urlsafe string from the given
         value.

        Returns:
            A string representing the signed value.

        Raises:
            TypeError: If the given signed value is not a string.
            SigningError: If a signature could not be created.
        """
        if not isinstance(value, str):
            raise TypeError(f"'signed_value' must be a string not {type(value)}")
        try:
            signer = signing.TimestampSigner()
            signed = signer.sign(value)
            signed_bytes = bytes(signed, encoding='utf-8')
            signed_urlsafe = base64.urlsafe_b64encode(signed_bytes).decode()
            return signed_urlsafe
        except Exception:
            raise SigningError(f"'{value}' could not be signed.")

    def unsign(self, signed_value, max_age=None):
        """Retrieves the original value from the given signed value and check
         it wasn't signed more than max_age seconds ago id provided.

        This method expects the given value to be signed and urlsafe.
        Args:
            signed_value: a string representing signed value.
            max_age: a non-negative integer representing the time, in seconds,
                that the signed value is considered valid. The default is None
                and it means that the signed value should not expire.

        Returns:
            A string representing the original value.

        Raises:
            TypeError: If the given signed value is not a string.
            ValueError: if the given max_age value is not a negative integer if
                provided.
            SignatureExpired: If the signature is expired.
            SigningError: If the given value could not be unsigned.
        """
        if not isinstance(signed_value, str):
            raise TypeError(f"'signed_value' must be a string not {type(signed_value)}")
        if max_age:
            if not isinstance(max_age, int):
                raise TypeError(f"'max_age' must be a string not {type(signed_value)}")
            if max_age < 0:
                raise ValueError(f"The given max_age, {max_age}, is a negative value")
        try:
            signed_bytes = bytes(signed_value, encoding='utf-8')
            signed = base64.urlsafe_b64decode(signed_bytes)
            signed = signed.decode()
            signer = signing.TimestampSigner()
            return signer.unsign(signed, max_age)
        except signing.SignatureExpired:
            raise
        except Exception:
            raise SigningError(f"'{signed_value}' could not be signed.")


SIGNER = Signer()
