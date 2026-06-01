import os
import json
import aiosqlite

from fastmcp import FastMCP

from db import DB_PATH

from auth import (
    authenticate_token,
    register_user,
    login_user,
    logout_user
)

# =========================================================
# MCP SERVER
# =========================================================

mcp = FastMCP("ExpenseTracker")

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)

# =========================================================
# MCP PROMPT
# =========================================================

@mcp.prompt()
def auth_prompt():

    return """
    Expense Tracker MCP Server

    Authentication Instructions:
    - Before using any expense-related tool, ask the user to login.
    - If the user is not registered, ask them to register first.
    - After successful login, store and reuse the returned token.
    - All expense tools require a valid token.

    Authentication Tools:
    - register(username, password)
    - login(username, password)
    - logout(token)

    Expense Tools:
    - add_expense
    - list_expenses
    - summarize
    - update_expense
    - delete_expense

    Never invoke expense tools without authentication.
    """

# =========================================================
# AUTH TOOLS
# =========================================================

@mcp.tool()
async def register(
    username: str,
    password: str
):

    """
    Register a new user.
    """

    try:

        return await register_user(
            username,
            password
        )

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
async def login(
    username: str,
    password: str
):

    """
    Login existing user and generate session token.
    """

    try:

        return await login_user(
            username,
            password
        )

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
async def logout(token: str):

    """
    Logout current session.
    """

    try:

        return await logout_user(token)

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# ADD EXPENSE
# =========================================================

@mcp.tool()
async def add_expense(
    token: str,
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):

    """
    Add a new expense.
    """

    try:

        user_id = await authenticate_token(token)


        if not user_id:

            return {
                "status": "error",
                "message": "Invalid or expired token"
            }

        async with aiosqlite.connect(DB_PATH) as c:

            cur = await c.execute(
                """
                INSERT INTO expenses
                (
                    user_id,
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                )
            )

            await c.commit()

            return {
                "status": "success",
                "id": cur.lastrowid,
                "message": "Expense added successfully"
            }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# LIST EXPENSES
# =========================================================

@mcp.tool()
async def list_expenses(
    token: str,
    start_date: str,
    end_date: str
):

    """
    List expenses within date range.
    """

    try:

        user_id = await authenticate_token(token)

        if not user_id:

            return {
                "status": "error",
                "message": "Invalid or expired token"
            }

        async with aiosqlite.connect(DB_PATH) as c:

            cur = await c.execute(
                """
                SELECT
                    id,
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                FROM expenses
                WHERE user_id = ?
                AND date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (
                    user_id,
                    start_date,
                    end_date
                )
            )

            cols = [d[0] for d in cur.description]

            rows = await cur.fetchall()

            return [
                dict(zip(cols, row))
                for row in rows
            ]

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# SUMMARIZE EXPENSES
# =========================================================

@mcp.tool()
async def summarize(
    token: str,
    start_date: str,
    end_date: str,
    category: str = None
):

    """
    Summarize expenses by category.
    """

    try:

        user_id = await authenticate_token(token)

        if not user_id:

            return {
                "status": "error",
                "message": "Invalid or expired token"
            }

        query = """
            SELECT
                category,
                SUM(amount) AS total_amount,
                COUNT(*) AS count
            FROM expenses
            WHERE user_id = ?
            AND date BETWEEN ? AND ?
        """

        params = [
            user_id,
            start_date,
            end_date
        ]

        if category:

            query += " AND category = ?"

            params.append(category)

        query += """
            GROUP BY category
            ORDER BY total_amount DESC
        """

        async with aiosqlite.connect(DB_PATH) as c:

            cur = await c.execute(query, params)

            cols = [d[0] for d in cur.description]

            rows = await cur.fetchall()

            return [
                dict(zip(cols, row))
                for row in rows
            ]

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# UPDATE EXPENSE
# =========================================================

@mcp.tool()
async def update_expense(
    token: str,
    expense_id: int,
    date: str = None,
    amount: float = None,
    category: str = None,
    subcategory: str = None,
    note: str = None
):

    """
    Update an existing expense.
    """

    try:

        user_id = await authenticate_token(token)

        if not user_id:

            return {
                "status": "error",
                "message": "Invalid or expired token"
            }

        fields = []

        values = []

        if date is not None:
            fields.append("date = ?")
            values.append(date)

        if amount is not None:
            fields.append("amount = ?")
            values.append(amount)

        if category is not None:
            fields.append("category = ?")
            values.append(category)

        if subcategory is not None:
            fields.append("subcategory = ?")
            values.append(subcategory)

        if note is not None:
            fields.append("note = ?")
            values.append(note)

        if not fields:

            return {
                "status": "error",
                "message": "No fields provided for update"
            }

        values.extend([
            user_id,
            expense_id
        ])

        async with aiosqlite.connect(DB_PATH) as c:

            cur = await c.execute(
                f"""
                UPDATE expenses
                SET {', '.join(fields)}
                WHERE user_id = ?
                AND id = ?
                """,
                values
            )

            await c.commit()

            if cur.rowcount == 0:

                return {
                    "status": "error",
                    "message": "Expense not found"
                }

            return {
                "status": "success",
                "message": "Expense updated successfully"
            }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# DELETE EXPENSE
# =========================================================

@mcp.tool()
async def delete_expense(
    token: str,
    expense_id: int
):

    """
    Delete an expense.
    """

    try:

        user_id = await authenticate_token(token)

        if not user_id:

            return {
                "status": "error",
                "message": "Invalid or expired token"
            }

        async with aiosqlite.connect(DB_PATH) as c:

            cur = await c.execute(
                """
                DELETE FROM expenses
                WHERE user_id = ?
                AND id = ?
                """,
                (
                    user_id,
                    expense_id
                )
            )

            await c.commit()

            if cur.rowcount == 0:

                return {
                    "status": "error",
                    "message": "Expense not found"
                }

            return {
                "status": "success",
                "message": "Expense deleted successfully"
            }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# MCP RESOURCE
# =========================================================

@mcp.resource(
    "expense:///categories",
    mime_type="application/json"
)
def categories():

    """
    Get available expense categories.
    """

    default_categories = {
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Other"
        ]
    }

    try:

        with open(
            CATEGORIES_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()

    except FileNotFoundError:

        return json.dumps(
            default_categories,
            indent=2
        )

    except Exception as e:

        return json.dumps({
            "error": str(e)
        })