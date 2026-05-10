import os
import asyncio
import requests
import re
from flask import Flask, jsonify, request
from telethon import TelegramClient, types
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest

app = Flask(__name__)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

BASE_URL = "https://t.me/"

# ================= TELETHON =================
loop = asyncio.get_event_loop()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

async def init():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Premium Bot Started Successfully")

loop.run_until_complete(init())

# ================= HELPER FUNCTIONS =================
def clean_html(text):
    return re.sub("<.*?>", "", text).strip() if text else "N/A"

def safe_get(obj, attr, default="N/A"):
    try:
        value = getattr(obj, attr, default)
        return value if value not in [None, ""] else default
    except:
        return default

# ================= MAIN ROUTE =================
@app.route("/")
def user_data():

    # দুইভাবেই ইনপুট নেওয়া যাবে
    # /?user=@username
    # /?chat_id=123456789

    username = request.args.get("user")
    chat_id = request.args.get("chat_id")

    if not username and not chat_id:
        return jsonify({
            "success": False,
            "error": "Please provide username or chat_id",
            "example_1": "/?user=@username",
            "example_2": "/?chat_id=123456789"
        }), 400

    try:

        async def fetch_telegram_info():

            # ================= ENTITY LOAD =================
            if username:

                if not username.startswith("@"):
                    username_fixed = "@" + username
                else:
                    username_fixed = username

                entity = await client.get_entity(username_fixed)
                target_value = username_fixed

            else:
                entity = await client.get_entity(int(chat_id))
                target_value = chat_id

            entity_id = entity.id

            data = {
                "success": True,
                "credit": "@sakib01994",
                "target": target_value,
                "id": entity_id,
                "access_hash": safe_get(entity, "access_hash"),
                "type": "Unknown"
            }

            # ================= USER INFO =================
            if isinstance(entity, types.User):

                data["type"] = "User"

                full = await client(GetFullUserRequest(entity))

                status = "Unknown"

                try:
                    if isinstance(entity.status, types.UserStatusOnline):
                        status = "Online"
                    elif isinstance(entity.status, types.UserStatusOffline):
                        status = "Offline"
                    elif isinstance(entity.status, types.UserStatusRecently):
                        status = "Recently Active"
                    elif isinstance(entity.status, types.UserStatusLastWeek):
                        status = "Last Week"
                    elif isinstance(entity.status, types.UserStatusLastMonth):
                        status = "Last Month"
                except:
                    pass

                data.update({

                    "first_name": safe_get(entity, "first_name"),
                    "last_name": safe_get(entity, "last_name"),
                    "username": safe_get(entity, "username"),
                    "phone": safe_get(entity, "phone", "Private"),
                    "bio": safe_get(full.full_user, "about"),

                    "common_chats": safe_get(
                        full.full_user,
                        "common_chats_count",
                        0
                    ),

                    "language_code": safe_get(entity, "lang_code"),

                    "status": status,

                    "is_bot": safe_get(entity, "bot", False),
                    "is_verified": safe_get(entity, "verified", False),
                    "is_scam": safe_get(entity, "scam", False),
                    "is_fake": safe_get(entity, "fake", False),
                    "is_support": safe_get(entity, "support", False),
                    "is_restricted": safe_get(entity, "restricted", False),
                    "premium_user": safe_get(entity, "premium", False),

                    "dc_id": safe_get(
                        entity.photo,
                        "dc_id"
                    ) if safe_get(entity, "photo", None) else "N/A",

                    "has_profile_photo": bool(entity.photo),

                    "can_pin_message": safe_get(
                        full.full_user,
                        "pinned_msg_id"
                    ),

                    "blocked": safe_get(
                        full.full_user,
                        "blocked",
                        False
                    ),

                    "contact": safe_get(
                        full.full_user,
                        "contact",
                        False
                    ),

                    "mutual_contact": safe_get(
                        full.full_user,
                        "mutual_contact",
                        False
                    ),

                    "stories_hidden": safe_get(
                        full.full_user,
                        "stories_hidden",
                        False
                    ),

                    "stories_unavailable": safe_get(
                        full.full_user,
                        "stories_unavailable",
                        False
                    )
                })

            # ================= GROUP / CHANNEL INFO =================
            elif isinstance(entity, (types.Chat, types.Channel)):

                data["type"] = (
                    "Channel"
                    if isinstance(entity, types.Channel)
                    and not entity.megagroup
                    else "Group"
                )

                full = await client(GetFullChannelRequest(entity))

                data.update({

                    "title": safe_get(entity, "title"),

                    "username": safe_get(entity, "username"),

                    "participants_count": safe_get(
                        full.full_chat,
                        "participants_count",
                        0
                    ),

                    "description": safe_get(
                        full.full_chat,
                        "about"
                    ),

                    "is_verified": safe_get(entity, "verified", False),

                    "is_scam": safe_get(entity, "scam", False),

                    "is_fake": safe_get(entity, "fake", False),

                    "is_restricted": safe_get(
                        entity,
                        "restricted",
                        False
                    ),

                    "is_megagroup": safe_get(
                        entity,
                        "megagroup",
                        False
                    ),

                    "gigagroup": safe_get(
                        entity,
                        "gigagroup",
                        False
                    ),

                    "broadcast": safe_get(
                        entity,
                        "broadcast",
                        False
                    ),

                    "creator": safe_get(
                        entity,
                        "creator",
                        False
                    ),

                    "linked_chat_id": safe_get(
                        full.full_chat,
                        "linked_chat_id"
                    ),

                    "slowmode_enabled": safe_get(
                        full.full_chat,
                        "slowmode_enabled",
                        False
                    ),

                    "can_view_participants": safe_get(
                        full.full_chat,
                        "can_view_participants",
                        False
                    ),

                    "can_set_username": safe_get(
                        full.full_chat,
                        "can_set_username",
                        False
                    ),

                    "has_scheduled": safe_get(
                        full.full_chat,
                        "has_scheduled",
                        False
                    ),

                    "has_hidden_members": safe_get(
                        full.full_chat,
                        "has_hidden_members",
                        False
                    ),

                    "has_private_forwards": safe_get(
                        full.full_chat,
                        "has_private_forwards",
                        False
                    ),

                    "has_protected_content": safe_get(
                        full.full_chat,
                        "has_protected_content",
                        False
                    ),

                    "dc_id": safe_get(
                        entity.photo,
                        "dc_id"
                    ) if safe_get(entity, "photo", None) else "N/A",

                    "has_profile_photo": bool(entity.photo)
                })

            # ================= PROFILE PHOTO =================
            try:
                photo = await client.download_profile_photo(
                    entity,
                    file=bytes
                )

                data["profile_photo_found"] = True if photo else False

            except:
                data["profile_photo_found"] = False

            # ================= PUBLIC SCRAPING =================
            try:

                public_username = safe_get(entity, "username")

                if public_username != "N/A":

                    tg_url = BASE_URL + public_username

                    web_res = requests.get(
                        tg_url,
                        headers={
                            "User-Agent": "Mozilla/5.0"
                        },
                        timeout=5
                    )

                    if web_res.status_code == 200:

                        html = web_res.text

                        web_photo = re.search(
                            r'photo_image.*?src="([^"]+)"',
                            html
                        )

                        web_members = re.search(
                            r'tgme_page_extra">(.*?)</div>',
                            html
                        )

                        data["public_view"] = {

                            "telegram_link": tg_url,

                            "web_image": (
                                web_photo.group(1)
                                if web_photo else None
                            ),

                            "status_bar": (
                                clean_html(web_members.group(1))
                                if web_members else "N/A"
                            )
                        }

            except:
                data["public_view"] = "Public scrape failed"

            return data

        # ================= FINAL RESULT =================
        final_result = loop.run_until_complete(fetch_telegram_info())

        return jsonify(final_result)

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ================= RUN =================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )