import uuid
import bcrypt
import aiosqlite

from datetime import datetime, timedelta

from db import DB_PATH

# In-memory session store

SESSIONS = {}

# =========================
# AUTH HELPERS
# =========================

async def authenticate_user(
    username: str,
    password: str
):

    async with aiosqlite.connect(DB_PATH) as c:

        cur = await c.execute(
            """
            SELECT id, password
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        user = await cur.fetchone()

        if not user:
            return None

        user_id, hashed_password = user

        if bcrypt.checkpw(
            password.encode(),
            hashed_password.encode()
        ):
            return user_id

        return None


async def authenticate_token(token: str):

    session = SESSIONS.get(token)

    if not session:
        return None

    if datetime.utcnow() > session["expires"]:

        del SESSIONS[token]

        return None

    return session["user_id"]

# =========================
# REGISTER
# =========================

async def register_user(
    username: str,
    password: str
):

    hashed_password = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    async with aiosqlite.connect(DB_PATH) as c:

        await c.execute(
            """
            INSERT INTO users(username, password)
            VALUES (?, ?)
            """,
            (username, hashed_password)
        )

        await c.commit()

    return {
        "status": "success",
        "message": "User registered successfully"
    }

# =========================
# LOGIN
# =========================

async def login_user(
    username: str,
    password: str
):

    user_id = await authenticate_user(
        username,
        password
    )

    if not user_id:

        return {
            "status": "error",
            "message": "Invalid username or password"
        }

    token = str(uuid.uuid4())

    SESSIONS[token] = {
        "user_id": user_id,
        "expires": datetime.utcnow() + timedelta(hours=24)
    }

    return {
        "status": "success",
        "token": token,
        "expires_in": "24 hours"
    }

# =========================
# LOGOUT
# =========================

async def logout_user(token: str):

    if token in SESSIONS:
        del SESSIONS[token]

    return {
        "status": "success",
        "message": "Logged out successfully"
    }