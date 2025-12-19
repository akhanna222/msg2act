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
    Initiate Google OAuth flow

    Returns:
        RedirectResponse: Redirect to Google's OAuth consent screen
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

    return RedirectResponse(url=authorization_url)


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

        # Create access token for our app
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        # In production, redirect to frontend with token
        # For now, return JSON response
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.full_name,
            },
            "message": "Gmail connected successfully! Email sync will begin shortly.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth flow failed: {str(e)}",
        )


@router.get("/auth/status")
async def auth_status(db: Session = Depends(get_db)):
    """
    Check authentication status and connected services

    Returns:
        dict: List of connected services for the user
    """
    # In production, this would require authentication
    # For now, just return sample data
    return {
        "authenticated": False,
        "message": "Please implement authentication middleware"
    }
