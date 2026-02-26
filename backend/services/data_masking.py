"""Data masking service."""

from typing import Optional


class DataMaskingService:
    """Service for masking sensitive data based on user role."""

    # Masking rules: field_name -> {role: strategy}
    # Strategies: full, partial, hidden
    MASKING_RULES = {
        "email": {
            "admin": "full",
            "support": "partial",
            "reader": "hidden",
            "writer": "hidden",
        },
        "phone": {
            "admin": "full",
            "support": "partial",
            "reader": "hidden",
            "writer": "hidden",
        },
        "ssn": {
            "admin": "full",
            "support": "partial",
            "reader": "hidden",
            "writer": "hidden",
        },
        "credit_card": {
            "admin": "full",
            "support": "partial",
            "reader": "hidden",
            "writer": "hidden",
        },
    }

    def mask_field(self, field_name: str, value: Optional[str], role: str) -> Optional[str]:
        """
        Mask a field value based on role.

        Args:
            field_name: Name of the field to mask
            value: Original value
            role: User role

        Returns:
            Masked value or [REDACTED]
        """
        if value is None:
            return None

        rules = self.MASKING_RULES.get(field_name, {})
        strategy = rules.get(role, "hidden")

        if strategy == "full":
            return value
        elif strategy == "partial":
            return self._partial_mask(field_name, value)
        else:  # hidden
            return "[REDACTED]"

    def _partial_mask(self, field_name: str, value: str) -> str:
        """Apply partial masking to a field value."""
        if field_name == "email":
            parts = value.split("@")
            if len(parts) == 2:
                user, domain = parts
                if len(user) > 2:
                    return f"{user[0]}***@{domain}"
                return f"***@{domain}"
            return "***@***"

        elif field_name == "phone":
            value = value.replace(" ", "").replace("-", "")
            if len(value) >= 7:
                return f"{value[:4]}***{value[-4:]}"
            return "*******"

        elif field_name == "ssn":
            parts = value.split("-")
            if len(parts) == 3:
                return f"***-**-{parts[2]}"
            return f"***-**-{value[-4:]}"

        elif field_name == "credit_card":
            value = value.replace(" ", "").replace("-", "")
            if len(value) >= 12:
                return f"{value[:4]}********{value[-4:]}"
            return "************"

        return "***"

    def mask_user(self, user: dict, role: str) -> dict:
        """Mask sensitive fields in a user dict."""
        result = user.copy()
        if "email" in result:
            result["email"] = self.mask_field("email", result["email"], role)
        if "phone" in result:
            result["phone"] = self.mask_field("phone", result["phone"], role)
        return result

    def mask_user_list(self, users: list, role: str) -> list:
        """Mask sensitive fields in a list of users."""
        return [self.mask_user(user, role) for user in users]


# Global instance
_masking_service: Optional[DataMaskingService] = None


def get_masking_service() -> DataMaskingService:
    """Get global masking service instance."""
    global _masking_service
    if _masking_service is None:
        _masking_service = DataMaskingService()
    return _masking_service
