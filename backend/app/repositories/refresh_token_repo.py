from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(RefreshToken, db)

    def get_active_by_jti(self, jti: str) -> RefreshToken | None:
        return (
            self.session.query(RefreshToken)
            .filter(
                RefreshToken.jti == jti,
                RefreshToken.revoked.is_(False),
            )
            .first()
        )

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return (
            self.session.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
        token.revoked_at = datetime.now()
        self.session.add(token)
        self.session.flush()

    def revoke_family(self, family_id: str) -> None:
        self.session.query(RefreshToken).filter(
            RefreshToken.family_id == family_id
        ).update({"revoked": True, "revoked_at": datetime.now()}, synchronize_session=False)

    def revoke_all_for_user(self, user_id: int) -> None:
        self.session.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).update({"revoked": True, "revoked_at": datetime.now()}, synchronize_session=False)

    def purge_expired(self, before: datetime | None = None) -> None:
        """Apaga tokens expirados/revogados há mais tempo (higiene)."""
        cutoff = before or (datetime.now() - timedelta(days=30))
        self.session.query(RefreshToken).filter(RefreshToken.expires_at < cutoff).delete()
        self.session.commit()

    @staticmethod
    def expire_days() -> timedelta:
        return timedelta(days=get_settings().REFRESH_TOKEN_EXPIRE_DAYS)