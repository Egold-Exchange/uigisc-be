from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.database import get_database
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, 
    VerificationRequest, SendVerificationRequest,
    SendVerificationCodeRequest, VerifyCodeRequest, VerificationCodeResponse,
    ForgotPasswordRequest, VerifyResetCodeRequest, ResetPasswordRequest
)
from app.services.auth import (
    get_password_hash, verify_password, create_access_token,
    generate_verification_token, is_admin_email
)
from app.services.email import send_verification_email
from app.services.sns import (
    send_verification_code_email, 
    verify_code,
    send_password_reset_code_email,
    generate_verification_code
)
from app.models.user import user_helper
from app.middleware.auth import get_current_user
from app.schemas.user import TokenData

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user with email, password, and subdomain."""
    db = get_database()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if subdomain is available
    existing_subdomain = await db.users.find_one({"subdomain": user_data.subdomain.lower()})
    if existing_subdomain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already taken"
        )
    
    # Determine role
    role = "admin" if is_admin_email(user_data.email) else "user"
    
    # Generate verification token (kept for future if needed)
    verification_token = generate_verification_token()
    
    # Create user document - Auto-verify for now
    user_doc = {
        "email": user_data.email.lower(),
        "password_hash": get_password_hash(user_data.password),
        "subdomain": user_data.subdomain.lower(),
        "name": user_data.name.strip(),
        "mobile": user_data.mobile.strip(),
        "role": role,
        "is_verified": True,  # Auto-verified as per request
        "verification_token": verification_token,
        "verification_token_expires": datetime.utcnow() + timedelta(hours=24),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    # Insert user
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    # Create website for user - Auto-publish
    website_doc = {
        "user_id": result.inserted_id,
        "subdomain": user_data.subdomain.lower(),
        "can_update_referral": True,
        "status": "active",  # Auto-active as per request
        "customizations": {},
        "created_at": datetime.utcnow(),
        "date_published": datetime.utcnow(),
        "last_modified": datetime.utcnow(),
    }
    await db.websites.insert_one(website_doc)
    
    # Send verification email is bypassed/async for now
    # await send_verification_email(user_data.email, verification_token, user_data.subdomain)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(result.inserted_id),
            "email": user_data.email.lower(),
            "role": role
        }
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=str(result.inserted_id),
            email=user_data.email.lower(),
            subdomain=user_data.subdomain.lower(),
            name=user_data.name.strip(),
            mobile=user_data.mobile.strip(),
            role=role,
            is_verified=True,
            created_at=user_doc["created_at"]
        )
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login with email and password."""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": credentials.email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user.get("role", "user")
        }
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            subdomain=user.get("subdomain"),
            name=user.get("name"),
            mobile=user.get("mobile"),
            role=user.get("role", "user"),
            is_verified=user.get("is_verified", False),
            created_at=user.get("created_at")
        )
    )


@router.post("/send-verification")
async def send_verification(request: SendVerificationRequest):
    """Send or resend verification email."""
    db = get_database()
    
    user = await db.users.find_one({"email": request.email.lower()})
    if not user:
        # Don't reveal if email exists
        return {"message": "If email exists, verification email has been sent"}
    
    if user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new token
    verification_token = generate_verification_token()
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "verification_token": verification_token,
                "verification_token_expires": datetime.utcnow() + timedelta(hours=24),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    await send_verification_email(
        user["email"], 
        verification_token, 
        user.get("subdomain", "")
    )
    
    return {"message": "Verification email sent"}


@router.post("/verify-email")
async def verify_email(request: VerificationRequest):
    """Verify email with token."""
    db = get_database()
    
    user = await db.users.find_one({
        "verification_token": request.token,
        "verification_token_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user and website
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "is_verified": True,
                "verification_token": None,
                "verification_token_expires": None,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Publish website
    await db.websites.update_one(
        {"user_id": user["_id"]},
        {
            "$set": {
                "status": "active",
                "date_published": datetime.utcnow(),
                "last_modified": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Email verified successfully"}


@router.post("/send-code", response_model=VerificationCodeResponse)
async def send_verification_code(request: SendVerificationCodeRequest):
    """
    Send a verification code to the user's email via AWS SES.
    Used during registration to verify email before creating account.
    """
    db = get_database()
    
    # Check if email is already registered
    existing_user = await db.users.find_one({"email": request.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please login instead."
        )
    
    # Send verification code
    result = await send_verification_code_email(request.email)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Failed to send verification code')
        )
    
    return VerificationCodeResponse(
        success=True,
        message=result.get('message', 'Verification code sent')
    )


@router.post("/verify-code")
async def verify_verification_code(request: VerifyCodeRequest):
    """
    Verify the code entered by the user.
    Returns success if the code is valid.
    """
    result = verify_code(request.email, request.code)
    
    if not result['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['message']
        )
    
    return {"verified": True, "message": result['message']}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current user information."""
    db = get_database()
    
    user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        subdomain=user.get("subdomain"),
        name=user.get("name"),
        mobile=user.get("mobile"),
        role=user.get("role", "user"),
        is_verified=user.get("is_verified", False),
        created_at=user.get("created_at")
    )


# ==================== FORGOT PASSWORD ENDPOINTS ====================

@router.post("/forgot-password", response_model=VerificationCodeResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send a password reset code to the user's email.
    Returns success even if email doesn't exist (security measure).
    """
    db = get_database()
    
    normalized_email = request.email.lower().strip()

    # Check if user exists
    user = await db.users.find_one({"email": normalized_email})
    
    # For security, always return success message even if user doesn't exist
    if not user:
        return VerificationCodeResponse(
            success=True,
            message="If an account exists with this email, a password reset code has been sent."
        )
    
    # Generate and persist reset code in DB (worker-safe across processes)
    reset_code = generate_verification_code()
    reset_expiry = datetime.utcnow() + timedelta(minutes=15)
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_code": reset_code,
                "password_reset_expires_at": reset_expiry,
                "password_reset_attempts": 0,
                "password_reset_verified": False,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Send password reset code email
    result = await send_password_reset_code_email(normalized_email, reset_code)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Failed to send password reset code')
        )
    
    return VerificationCodeResponse(
        success=True,
        message="If an account exists with this email, a password reset code has been sent."
    )


@router.post("/verify-reset-code")
async def verify_reset_code(request: VerifyResetCodeRequest):
    """
    Verify the password reset code.
    Must be called before reset-password to validate the code.
    """
    db = get_database()
    
    normalized_email = request.email.lower().strip()

    # Check if user exists
    user = await db.users.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or code"
        )

    stored_code = user.get("password_reset_code")
    expires_at = user.get("password_reset_expires_at")
    attempts = user.get("password_reset_attempts", 0)
    provided_code = request.code.strip()

    if not stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset code found. Please request a new code."
        )

    if not expires_at or datetime.utcnow() > expires_at:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$unset": {
                "password_reset_code": "",
                "password_reset_expires_at": "",
                "password_reset_attempts": "",
                "password_reset_verified": "",
            }}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset code has expired. Please request a new code."
        )

    if attempts >= 5:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$unset": {
                "password_reset_code": "",
                "password_reset_expires_at": "",
                "password_reset_attempts": "",
                "password_reset_verified": "",
            }}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please request a new code."
        )

    if stored_code != provided_code:
        next_attempts = attempts + 1
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"password_reset_attempts": next_attempts}}
        )
        remaining = max(0, 5 - next_attempts)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code. {remaining} attempts remaining."
        )

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_reset_verified": True}}
    )

    return {"verified": True, "message": "Code verified successfully. You can now reset your password."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset the user's password after code verification.
    The code must have been verified via /verify-reset-code first.
    """
    db = get_database()
    
    normalized_email = request.email.lower().strip()

    # Check if user exists
    user = await db.users.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request"
        )

    stored_code = user.get("password_reset_code")
    expires_at = user.get("password_reset_expires_at")
    attempts = user.get("password_reset_attempts", 0)
    verified = user.get("password_reset_verified", False)
    provided_code = request.code.strip()

    if not stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset code found. Please request a new code."
        )

    if not expires_at or datetime.utcnow() > expires_at:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$unset": {
                "password_reset_code": "",
                "password_reset_expires_at": "",
                "password_reset_attempts": "",
                "password_reset_verified": "",
            }}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset code has expired. Please request a new code."
        )

    if not verified:
        if attempts >= 5:
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$unset": {
                    "password_reset_code": "",
                    "password_reset_expires_at": "",
                    "password_reset_attempts": "",
                    "password_reset_verified": "",
                }}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many failed attempts. Please request a new code."
            )

        if stored_code != provided_code:
            next_attempts = attempts + 1
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"password_reset_attempts": next_attempts}}
            )
            remaining = max(0, 5 - next_attempts)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid code. {remaining} attempts remaining."
            )
    
    # Update the password
    new_password_hash = get_password_hash(request.new_password)
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "password_reset_code": "",
                "password_reset_expires_at": "",
                "password_reset_attempts": "",
                "password_reset_verified": "",
            }
        }
    )

    return {"success": True, "message": "Password has been reset successfully. You can now log in with your new password."}
