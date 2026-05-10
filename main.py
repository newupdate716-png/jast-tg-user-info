import os
import re
import asyncio
import requests

from flask import Flask, jsonify, request

from telethon import TelegramClient, types
from telethon.sessions import StringSession

from telethon.errors import (
    UsernameInvalidError,
    UsernameNotOccupiedError
)

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest

# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

BASE_URL = "https://t.me/"

# =========================================================
# EVENT LOOP FIX
# =========================================================

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH,
    loop=loop
)

# =========================================================
# START CLIENT
# =========================================================

async def start_client():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Premium Telegram API Started")

try:
    loop.run_until_complete(start_client())
except Exception as e:
    print(f"❌ START ERROR: {e}")

# =========================================================
# HELPERS
# =========================================================

def safe_get(obj, attr, default="N/A"):
    try:
        value = getattr(obj, attr, default)
        return value if value not in [None, ""] else default
    except:
        return default

def clean_html(text):
    return re.sub("<.*?>", "", text).strip() if text else "N/A"

# =========================================================
# PREMIUM ENTITY RESOLVER
# =========================================================

async def resolve_entity(user=None, chat_id=None):

    # =========================================
    # USERNAME SYSTEM
    # =========================================

    if user:

        if not user.startswith("@"):
            user = "@" + user

        try:
            return await client.get_entity(user)

        except UsernameInvalidError:
            raise Exception("Invalid username")

        except UsernameNotOccupiedError:
            raise Exception("Username not found")

    # =========================================
    # CHAT ID SYSTEM
    # =========================================

    if chat_id:

        try:
            chat_id = int(chat_id)

        except:
            raise Exception("Invalid chat_id")

        # =====================================
        # TRY INPUT ENTITY
        # =====================================

        try:
            return await client.get_input_entity(chat_id)

        except:
            pass

        # =====================================
        # TRY DIRECT ENTITY
        # =====================================

        try:
            return await client.get_entity(chat_id)

        except:
            pass

        # =====================================
        # SEARCH DIALOGS
        # =====================================

        try:

            async for dialog in client.iter_dialogs():

                entity = dialog.entity

                if getattr(entity, "id", None) == abs(chat_id):
                    return entity

        except:
            pass

        raise Exception(
            "Entity not found in session. "
            "User/Group/Channel must exist in account dialogs."
        )

    raise Exception("No username or chat_id provided")

# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "success": True,
        "service": "Premium Telegram Info API",
        "status": "running"
    })

# =========================================================
# MAIN API
# =========================================================

@app.route("/")
def telegram_info():

    username = request.args.get("user")
    chat_id = request.args.get("chat_id")

    if not username and not chat_id:

        return jsonify({
            "success": False,
            "error": "Provide user or chat_id",
            "example_1": "/?user=durov",
            "example_2": "/?chat_id=777000"
        }), 400

    try:

        async def fetch():

            entity = await resolve_entity(
                user=username,
                chat_id=chat_id
            )

            # =====================================
            # FIX INPUT ENTITY ISSUE
            # =====================================

            if not isinstance(
                entity,
                (types.User, types.Chat, types.Channel)
            ):
                entity = await client.get_entity(entity)

            data = {
                "success": True,
                "credit": "@sakib01994",
                "id": safe_get(entity, "id"),
                "access_hash": safe_get(entity, "access_hash"),
                "type": "Unknown"
            }

            # =====================================
            # USER INFO
            # =====================================

            if isinstance(entity, types.User):

                data["type"] = "User"

                full = await client(
                    GetFullUserRequest(entity)
                )

                status = "Unknown"

                try:

                    if isinstance(
                        entity.status,
                        types.UserStatusOnline
                    ):
                        status = "Online"

                    elif isinstance(
                        entity.status,
                        types.UserStatusOffline
                    ):
                        status = "Offline"

                    elif isinstance(
                        entity.status,
                        types.UserStatusRecently
                    ):
                        status = "Recently Active"

                    elif isinstance(
                        entity.status,
                        types.UserStatusLastWeek
                    ):
                        status = "Last Week"

                    elif isinstance(
                        entity.status,
                        types.UserStatusLastMonth
                    ):
                        status = "Last Month"

                except:
                    pass

                data.update({

                    "first_name":
                        safe_get(entity, "first_name"),

                    "last_name":
                        safe_get(entity, "last_name"),

                    "username":
                        safe_get(entity, "username"),

                    "phone":
                        safe_get(entity, "phone", "Private"),

                    "bio":
                        safe_get(full.full_user, "about"),

                    "common_chats":
                        safe_get(
                            full.full_user,
                            "common_chats_count",
                            0
                        ),

                    "language_code":
                        safe_get(entity, "lang_code"),

                    "status":
                        status,

                    "premium":
                        safe_get(entity, "premium", False),

                    "verified":
                        safe_get(entity, "verified", False),

                    "scam":
                        safe_get(entity, "scam", False),

                    "fake":
                        safe_get(entity, "fake", False),

                    "bot":
                        safe_get(entity, "bot", False),

                    "restricted":
                        safe_get(entity, "restricted", False),

                    "dc_id":
                        (
                            safe_get(entity.photo, "dc_id")
                            if entity.photo else "N/A"
                        ),

                    "has_photo":
                        bool(entity.photo)
                })

            # =====================================
            # GROUP / CHANNEL INFO
            # =====================================

            elif isinstance(
                entity,
                (types.Chat, types.Channel)
            ):

                full = await client(
                    GetFullChannelRequest(entity)
                )

                is_channel = (
                    isinstance(entity, types.Channel)
                    and not entity.megagroup
                )

                data["type"] = (
                    "Channel"
                    if is_channel
                    else "Group"
                )

                data.update({

                    "title":
                        safe_get(entity, "title"),

                    "username":
                        safe_get(entity, "username"),

                    "description":
                        safe_get(full.full_chat, "about"),

                    "participants":
                        safe_get(
                            full.full_chat,
                            "participants_count",
                            0
                        ),

                    "verified":
                        safe_get(entity, "verified", False),

                    "megagroup":
                        safe_get(entity, "megagroup", False),

                    "gigagroup":
                        safe_get(entity, "gigagroup", False),

                    "broadcast":
                        safe_get(entity, "broadcast", False),

                    "creator":
                        safe_get(entity, "creator", False),

                    "restricted":
                        safe_get(entity, "restricted", False),

                    "linked_chat_id":
                        safe_get(
                            full.full_chat,
                            "linked_chat_id"
                        ),

                    "slowmode":
                        safe_get(
                            full.full_chat,
                            "slowmode_enabled",
                            False
                        ),

                    "protected_content":
                        safe_get(
                            full.full_chat,
                            "has_protected_content",
                            False
                        ),

                    "hidden_members":
                        safe_get(
                            full.full_chat,
                            "has_hidden_members",
                            False
                        ),

                    "dc_id":
                        (
                            safe_get(entity.photo, "dc_id")
                            if entity.photo else "N/A"
                        ),

                    "has_photo":
                        bool(entity.photo)
                })

            # =====================================
            # PROFILE PHOTO CHECK
            # =====================================

            try:

                photo = await client.download_profile_photo(
                    entity,
                    file=bytes
                )

                data["profile_photo_found"] = bool(photo)

            except:
                data["profile_photo_found"] = False

            # =====================================
            # PUBLIC SCRAPE
            # =====================================

            try:

                public_username = safe_get(
                    entity,
                    "username"
                )

                if public_username != "N/A":

                    tg_url = BASE_URL + public_username

                    r = requests.get(
                        tg_url,
                        headers={
                            "User-Agent":
                            "Mozilla/5.0"
                        },
                        timeout=10
                    )

                    if r.status_code == 200:

                        html = r.text

                        web_photo = re.search(
                            r'photo_image.*?src="([^"]+)"',
                            html
                        )

                        web_extra = re.search(
                            r'tgme_page_extra">(.*?)</div>',
                            html
                        )

                        data["public_view"] = {

                            "telegram_link":
                                tg_url,

                            "web_photo":
                                (
                                    web_photo.group(1)
                                    if web_photo else None
                                ),

                            "extra":
                                (
                                    clean_html(
                                        web_extra.group(1)
                                    )
                                    if web_extra else "N/A"
                                )
                        }

            except:
                data["public_view"] = "Failed"

            return data

        result = loop.run_until_complete(fetch())

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    PORT = int(
        os.environ.get("PORT", 8080)
    )

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )