import os
import asyncio
import requests
import re
from flask import Flask, jsonify, request
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest

app = Flask(__name__)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

API_URL = "https://devil.elementfx.com/api.php?key=DEVIL&type=tg_number&term="
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

# ================= MAIN ROUTE =================
@app.route("/")
def user_data():
    # ইউজারনেম কুয়েরি প্যারামিটার থেকে নেওয়া হচ্ছে (?user=@username)
    username = request.args.get('user')
    
    if not username:
        return jsonify({
            "success": False, 
            "error": "Please provide a username. Usage: /?user=@username"
        }), 400

    try:
        if not username.startswith("@"):
            username = "@" + username
        
        clean_username = username.replace("@", "")
        tg_url = BASE_URL + clean_username

        async def fetch_telegram_info():
            # ১. এনটিটি খুঁজে বের করা
            entity = await client.get_entity(username)
            entity_id = entity.id
            
            data = {
                "success": True,
                "credit": "@sakib01994",
                "target": username,
                "id": entity_id,
                "type": "Unknown"
            }

            # ২. প্রোফাইল টাইপ অনুযায়ী বিস্তারিত তথ্য আনা
            if isinstance(entity, types.User):
                data["type"] = "User"
                full = await client(GetFullUserRequest(entity))
                data.update({
                    "first_name": entity.first_name or "N/A",
                    "last_name": entity.last_name or "N/A",
                    "username": entity.username,
                    "phone": entity.phone or "Private",
                    "bio": full.full_user.about or "N/A",
                    "common_chats": full.full_user.common_chats_count,
                    "is_bot": entity.bot,
                    "is_verified": entity.verified,
                    "is_scam": entity.scam,
                    "is_fake": entity.fake,
                    "premium_user": getattr(entity, 'premium', False)
                })
            
            elif isinstance(entity, (types.Chat, types.Channel)):
                data["type"] = "Channel" if isinstance(entity, types.Channel) and not entity.megagroup else "Group"
                full = await client(GetFullChannelRequest(entity))
                data.update({
                    "title": entity.title,
                    "username": entity.username,
                    "participants_count": full.full_chat.participants_count or 0,
                    "description": full.full_chat.about or "N/A",
                    "is_verified": entity.verified,
                    "is_scam": entity.scam,
                    "is_restricted": entity.restricted,
                    "linked_chat_id": full.full_chat.linked_chat_id
                })

            # ৩. প্রোফাইল পিকচার চেক
            photo_path = await client.download_profile_photo(entity, file=bytes)
            data["has_profile_pic"] = True if photo_path else False

            # ৪. External Number API
            try:
                num_res = requests.get(API_URL + str(entity_id), timeout=5).json()
                if num_res.get("success"):
                    data["leaked_info"] = num_res.get("result")
                else:
                    data["leaked_info"] = "No leak data found"
            except:
                data["leaked_info"] = "API Timeout"

            # ৫. Public Web Scraping (ইমেজ লিঙ্কের জন্য)
            try:
                web_res = requests.get(tg_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                if web_res.status_code == 200:
                    html = web_res.text
                    web_photo = re.search(r'photo_image.*?src="([^"]+)"', html)
                    web_members = re.search(r'tgme_page_extra">(.*?)</div>', html)
                    
                    data["public_view"] = {
                        "web_image": web_photo.group(1) if web_photo else None,
                        "status_bar": clean_html(web_members.group(1)) if web_members else "N/A",
                        "telegram_link": tg_url
                    }
            except:
                data["public_view"] = "Web scraping failed"

            return data

        # লুপ রান করা
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
    app.run(host="0.0.0.0", port=port, debug=False)