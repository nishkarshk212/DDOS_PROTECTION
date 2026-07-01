import asyncio
from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from app.config import settings
from app.blocklist import blocklist_manager
import psutil

bot_client = None

def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_user_id

def get_main_keyboard():
    auto_text = "🔄 Auto-Block: ON" if blocklist_manager.auto_block_enabled else "🔄 Auto-Block: OFF"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Block IP", callback_data="btn_block"),
            InlineKeyboardButton("Unblock IP", callback_data="btn_unblock")
        ],
        [
            InlineKeyboardButton("View Blocklist", callback_data="btn_view"),
            InlineKeyboardButton(auto_text, callback_data="btn_toggle_auto")
        ],
        [
            InlineKeyboardButton("📈 Server Status", callback_data="btn_status"),
            InlineKeyboardButton("🧹 Flush All", callback_data="btn_flush")
        ]
    ])

async def start_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("⛔️ Unauthorized access.", parse_mode=enums.ParseMode.HTML)
    
    text = (
        "🛡 <b>DDoS Protection Control Panel</b>\n\n"
        "Use the buttons below to manage the API firewall."
    )
    await message.reply(text, reply_markup=get_main_keyboard(), parse_mode=enums.ParseMode.HTML)

async def block_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /block <ip_address>")
        
    ip = args[1]
    success = await blocklist_manager.add_ip(ip, reason="Manual Command", banned_by="Admin")
    
    if success:
        await message.reply(f"✅ Successfully blocked <code>{ip}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply(f"⚠️ <code>{ip}</code> is already blocked.", parse_mode=enums.ParseMode.HTML)

async def unblock_cmd(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /unblock <ip_address>")
        
    ip = args[1]
    success = await blocklist_manager.remove_ip(ip)
    
    if success:
        await message.reply(f"✅ Successfully unblocked <code>{ip}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply(f"⚠️ <code>{ip}</code> was not in the blocklist.", parse_mode=enums.ParseMode.HTML)

async def callback_handler(client: Client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("Unauthorized", show_alert=True)
        
    if query.data == "btn_block":
        await query.message.reply("Send <code>/block &lt;ip&gt;</code> to block an IP.", parse_mode=enums.ParseMode.HTML)
        await query.answer()
        
    elif query.data == "btn_unblock":
        await query.message.reply("Send <code>/unblock &lt;ip&gt;</code> to unblock an IP.", parse_mode=enums.ParseMode.HTML)
        await query.answer()
        
    elif query.data == "btn_view":
        ips = blocklist_manager.get_blocked_ips()
        if not ips:
            await query.answer("Blocklist is currently empty.", show_alert=True)
            return
            
        text = "📊 <b>Currently Blocked IPs:</b>\n\n"
        for ip, data in ips.items():
            text += f"▪️ <code>{ip}</code> (Reason: {data.get('reason')})\n"
            
        await query.message.reply(text, parse_mode=enums.ParseMode.HTML)
        await query.answer()

    elif query.data == "btn_toggle_auto":
        new_state = blocklist_manager.toggle_auto_block()
        state_text = "ON" if new_state else "OFF"
        await query.answer(f"Auto-Block is now {state_text}", show_alert=False)
        try:
            await query.edit_message_reply_markup(reply_markup=get_main_keyboard())
        except Exception:
            pass

    elif query.data == "btn_flush":
        count = await blocklist_manager.flush_all()
        await query.answer(f"Flushed {count} IPs from blocklist and OS firewall!", show_alert=True)

    elif query.data == "btn_status":
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        text = (
            "📈 <b>Server Status</b>\n\n"
            f"<b>CPU Usage:</b> {cpu}%\n"
            f"<b>RAM Usage:</b> {ram.percent}% ({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)\n"
            f"<b>Disk Usage:</b> {disk.percent}%\n"
        )
        await query.message.reply(text, parse_mode=enums.ParseMode.HTML)
        await query.answer()

async def start_bot():
    global bot_client
    if not settings.bot_token or not settings.admin_user_id:
        print("Warning: bot_token or admin_user_id not set in config. Bot will not start.")
        return

    print("Initializing Pyrogram on current event loop...")
    bot_client = Client(
        "ddos_bot",
        api_id=2040,
        api_hash="b18441a1ff607e10a989891a5462e627",
        bot_token=settings.bot_token,
        in_memory=True
    )

    # Register handlers
    bot_client.add_handler(MessageHandler(start_cmd, filters.command(["start", "menu"])))
    bot_client.add_handler(MessageHandler(block_cmd, filters.command("block")))
    bot_client.add_handler(MessageHandler(unblock_cmd, filters.command("unblock")))
    bot_client.add_handler(CallbackQueryHandler(callback_handler))

    try:
        await bot_client.start()
        print("DDoS Protection Bot Started Successfully!")
    except Exception as e:
        print(f"Failed to start bot: {e}")
