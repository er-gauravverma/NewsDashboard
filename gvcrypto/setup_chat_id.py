#!/usr/bin/env python3
"""
gvcrypto — Setup Helper
Run this script ONCE to find your Telegram chat_id.

Steps:
  1. Open Telegram and send ANY message to @gvalgo1979bot
  2. Run this script: python3 setup_chat_id.py
  3. Copy the chat_id printed below
  4. Paste it into config.json under telegram.chat_id
"""

import json
import os
import sys

import requests

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")


def get_chat_id(bot_token: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    print(f"\n🔍 Calling Telegram getUpdates API...")

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error contacting Telegram API: {e}")
        sys.exit(1)

    if not data.get("ok"):
        print(f"❌ Telegram API error: {data}")
        sys.exit(1)

    updates = data.get("result", [])
    if not updates:
        print(
            "\n⚠️  No messages received yet.\n"
            "   Please send a message to @gvalgo1979bot on Telegram first,\n"
            "   then re-run this script.\n"
        )
        sys.exit(0)

    print("\n✅ Found the following chats that have messaged your bot:\n")
    seen = set()
    for update in updates:
        msg = update.get("message") or update.get("channel_post") or {}
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type", "unknown")
        title = chat.get("title") or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
        username = chat.get("username", "")

        if chat_id and chat_id not in seen:
            seen.add(chat_id)
            label = f"@{username}" if username else title
            print(f"  • chat_id: {chat_id}  |  type: {chat_type}  |  name: {label}")

    if seen:
        chat_id_to_use = list(seen)[-1]
        print(f"\n👉 Suggested chat_id to use: {chat_id_to_use}")
        answer = input("\nUpdate config.json with this chat_id automatically? [y/N]: ").strip().lower()
        if answer == "y":
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            config["telegram"]["chat_id"] = chat_id_to_use
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            print(f"✅ config.json updated with chat_id: {chat_id_to_use}")
        else:
            print(f"ℹ️  Manually set 'chat_id' to {chat_id_to_use} in config.json")


def main():
    print("=" * 50)
    print("  gvcrypto — Telegram Chat ID Setup")
    print("=" * 50)

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please ensure it exists first.")
        sys.exit(1)

    bot_token = config["telegram"]["bot_token"]
    print(f"\n🤖 Bot token loaded from config.json")
    print(f"   Token: ...{bot_token[-10:]}")

    get_chat_id(bot_token)


if __name__ == "__main__":
    main()
