"""Import every model so `Base.metadata` is fully populated for Alembic."""

from app.models.ai_cache import AICache
from app.models.ai_invocation import AIInvocation
from app.models.asset import Asset, AssetFolder
from app.models.audit import Audit, AuditCategoryResult, AuditFinding
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.content_plan import ContentPlan
from app.models.content_sample import ContentSample
from app.models.email_verification import EmailVerification
from app.models.feature_flag import FeatureFlag, UserFeatureFlag
from app.models.job import Job
from app.models.job_description import JobDescription
from app.models.linkedin_connection import LinkedInConnection
from app.models.login_attempt import LoginAttempt
from app.models.oauth_identity import OAuthIdentity
from app.models.oauth_login_state import OAuthLoginState
from app.models.password_reset import PasswordReset
from app.models.plan_limit import PlanLimit
from app.models.profile_import import ProfileImportBlob, ProfileImportRow
from app.models.profile_snapshot import ProfileSnapshotRow
from app.models.recommendation import Recommendation
from app.models.refresh_token import RefreshToken
from app.models.resume import Resume
from app.models.resume_match import ResumeMatch
from app.models.score_history import ScoreHistory
from app.models.tool_run import ToolRun
from app.models.usage_counter import UsageCounter
from app.models.user import User
from app.models.voice_profile import VoiceProfile

__all__ = [
    "AICache",
    "AIInvocation",
    "Asset",
    "AssetFolder",
    "Audit",
    "AuditCategoryResult",
    "AuditFinding",
    "AuditLog",
    "Base",
    "ContentPlan",
    "ContentSample",
    "EmailVerification",
    "FeatureFlag",
    "Job",
    "JobDescription",
    "LinkedInConnection",
    "LoginAttempt",
    "OAuthIdentity",
    "OAuthLoginState",
    "PasswordReset",
    "PlanLimit",
    "ProfileImportBlob",
    "ProfileImportRow",
    "ProfileSnapshotRow",
    "Recommendation",
    "RefreshToken",
    "Resume",
    "ResumeMatch",
    "ScoreHistory",
    "ToolRun",
    "UsageCounter",
    "User",
    "UserFeatureFlag",
    "VoiceProfile",
]
