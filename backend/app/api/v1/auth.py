"""
Authentication endpoints including OAuth flows
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.database import get_db
from app.core.config import settings
from app.core.security import encrypt_token, create_access_token
from app.models.user import User
from app.models.oauth_token import OAuthToken
from app.models.data_source import DataSource

router = APIRouter()


@router.get("/auth/google/connect")
async def google_oauth_connect():
    """
    Get Google OAuth authorization URL

    Returns:
        str: Google OAuth authorization URL
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=settings.GOOGLE_SCOPES,
    )

    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent to get refresh token
    )

    # Return URL as plain string for frontend to redirect
    return authorization_url


@router.get("/auth/google/callback")
async def google_oauth_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback

    Args:
        code: Authorization code from Google
        db: Database session

    Returns:
        dict: Access token and user information
    """
    try:
        # Exchange authorization code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=settings.GOOGLE_SCOPES,
        )

        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Get user info from Google
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()

        email = user_info.get("email")
        name = user_info.get("name")
        google_user_id = user_info.get("id")

        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name=name,
                is_verified=True,
                last_login_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.last_login_at = datetime.utcnow()
            db.commit()

        # Store encrypted OAuth tokens
        oauth_token = (
            db.query(OAuthToken)
            .filter(
                OAuthToken.user_id == user.id,
                OAuthToken.provider == "google",
            )
            .first()
        )

        if oauth_token:
            # Update existing token
            oauth_token.access_token = encrypt_token(credentials.token)
            if credentials.refresh_token:
                oauth_token.refresh_token = encrypt_token(credentials.refresh_token)
            oauth_token.expires_at = credentials.expiry
            oauth_token.updated_at = datetime.utcnow()
        else:
            # Create new token
            oauth_token = OAuthToken(
                user_id=user.id,
                provider="google",
                access_token=encrypt_token(credentials.token),
                refresh_token=encrypt_token(credentials.refresh_token) if credentials.refresh_token else None,
                expires_at=credentials.expiry,
                scopes=" ".join(settings.GOOGLE_SCOPES),
                provider_user_id=google_user_id,
                provider_email=email,
            )
            db.add(oauth_token)

        db.commit()

        # Create or update Gmail data source
        gmail_source = (
            db.query(DataSource)
            .filter(
                DataSource.user_id == user.id,
                DataSource.source_type == "gmail",
            )
            .first()
        )

        if not gmail_source:
            gmail_source = DataSource(
                user_id=user.id,
                source_type="gmail",
                source_name=f"Gmail ({email})",
                status="connected",
                is_active=True,
                sync_enabled=True,
            )
            db.add(gmail_source)
            db.commit()
        else:
            gmail_source.status = "connected"
            gmail_source.updated_at = datetime.utcnow()
            db.commit()

        # Trigger email sync task
        try:
            from app.tasks.email_tasks import sync_gmail_account
            sync_gmail_account.delay(str(user.id), historical_days=30)
        except Exception as sync_error:
            print(f"Failed to trigger sync task: {sync_error}")

        # Redirect to frontend with success
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:5173"
        return RedirectResponse(url=f"{frontend_url}/dashboard?gmail_connected=true")

    except Exception as e:
        # Redirect to frontend with error
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:5173"
        return RedirectResponse(url=f"{frontend_url}/dashboard?gmail_error={str(e)}")


@router.get("/data-sources")
async def get_data_sources(db: Session = Depends(get_db)):
    """
    Get all data sources (connected accounts)

    Returns:
        dict: List of data sources
    """
    # For MVP, return all data sources without authentication
    # In production, this would be filtered by authenticated user
    sources = db.query(DataSource).filter(DataSource.is_active == True).all()

    return {
        "sources": [
            {
                "id": str(source.id),
                "source_type": source.source_type,
                "source_name": source.source_name,
                "status": source.status,
                "last_sync_at": source.last_sync_at.isoformat() if source.last_sync_at else None,
                "total_items_synced": source.total_items_synced,
            }
            for source in sources
        ]
    }
