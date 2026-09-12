"""Import every model so `Base.metadata` is fully populated for Alembic."""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.email_verification import EmailVerification
from app.models.feature_flag import FeatureFlag, UserFeatureFlag
from app.models.login_attempt import LoginAttempt
from app.models.oauth_identity import OAuthIdentity
from app.models.oauth_login_state import OAuthLoginState
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = [
    "AuditLog",
    "Base",
    "EmailVerification",
    "FeatureFlag",
    "LoginAttempt",
    "OAuthIdentity",
    "OAuthLoginState",
    "PasswordReset",
    "RefreshToken",
    "User",
    "UserFeatureFlag",
]
