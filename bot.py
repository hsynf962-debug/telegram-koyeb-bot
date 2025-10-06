import os
import asyncio 
from telegram import Update
from telegram.ext import (
    Application, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    CommandHandler, 
    CallbackContext,
)
from google import genai 
from google.genai.errors import APIError

# Your Bot Token (توکن شما از تلگرام)
# توجه: بهتر است این توکن را نیز به عنوان یک متغیر محیطی (مثلا BOT_TOKEN) تنظیم کنید.
TOKEN = '7313799357:AAEX6lK-9zFhQwkclXmDo094MR1dMDFr5E' 

# --- دیتابیس موقت (برای ثبت مشخصات) ---
USER_INFO = {} 
GROUP_IDS = [] 

# Initialize the Gemini client. 
try:
    # کلید API از متغیرهای محیطی Termux یا Koyeb خوانده می‌شود
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("CRITICAL: GEMINI_API_KEY not found in environment variables.")
        client = None
    else:
        client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Gemini Client Initialization Error: {e}")
    client = None

# متغیرهای محیطی Koyeb (اگر در Termux نباشند، ربات در حالت Polling اجرا می‌شود)
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

SYSTEM_INSTRUCTION = "شما یک کمدین و طنزپرداز حرفه‌ای به نام **شیطون بلا** هستید. لحن شما باید همیشه بسیار شوخ، طنزآمیز و شیطنت‌آمیز باشد. لحن طنز را همیشه بالا نگه دارید و خود را یک موجودیت باهوش و خنده‌دار فرض کنید. پاسخ‌هایتان باید به فارسی، کوتاه و بسیار گیرا باشند."

# --- تابع چت هوش مصنوعی (AI Chat) ---
# این تابع برای حل خطای NameError در Koyeb اضافه شد.
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if client is None:
        await update.message.reply_text("متاسفم! شیطون بلا خاموش شده (کلید API جِمینی پیدا نشد).")
        return

    # ابتدا فیلترهای ثبت مشخصات را چک می‌کنیم تا اگر پیام مربوط به آن بود، پاسخش را بدهیم و به Gemini نفرستیم.
    if await save_user_info(update, context):
        return
        
    if await show_user_info(update, context):
        return

    try:        # منطق نادیده گرفتن در گروه: اگر ربات منشن نشده باشد، پیامی ارسال نمی‌شود.
        if update.message.chat.type in ["group", "supergroup"]:
            if update.message.text and f"@{context.bot.username}" not in update.message.text:
                return
            # حذف منشن ربات در صورت وجود
            prompt = update.message.text.replace(f"@{context.bot.username}", "").strip()
        else:
            # چت خصوصی
            prompt = update.message.text
        
        # اگر پیام فقط حاوی 'ثبت اصل من:' بود و اطلاعاتی نداشت
        if len(prompt) < 2:
            return

        
        # اگر پیام فقط حاوی 'ثبت اصل من:' بود و اطلاعاتی نداشت
        if len(prompt) < 2:
            return

        # ارسال پیام به Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )
        
        await update.message.reply_text(response.text)
        
    except APIError as e:
        print(f"Gemini API Error: {e}")
        await update.message.reply_text("آی! یه مشکلی در ارتباط با جِمینی پیش اومده. کلید API رو چک کن.")
    except Exception as e:
        print(f"General Error in ai_chat: {e}")
        await update.message.reply_text("فکر کنم یه شوخی بزرگ شده! یه خطای ناشناخته رخ داد. 🤯")


# --- توابع مدیریتی گروه و ابزارهای ربات ---

async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        try:
            me = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
            if me.status in ["administrator", "creator"]:
                await update.message.reply_text("من یک مدیر هستم و می‌توانم گروه را مدیریت کنم. مجوزهایم را چک کنید.")
            else:
                await update.message.reply_text("من عضو هستم، اما برای مدیریت (مثل حذف پیام) باید من را به عنوان مدیر گروه ارتقاء دهید.")
        except Exception as e:
            print(f"Error checking admin status: {e}")
            await update.message.reply_text("خطا در بررسی وضعیت مدیر: آیا ربات به این گروه اضافه شده است؟")
    else:
        await update.message.reply_text("این دستور فقط در گروه‌ها قابل استفاده است.")

# تابع جدید: نمایش وظایف ربات
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks_list = (
        "🎉 **شیطون بلا** هستم! وظایف من اینهاست: 🎉\n\n"
        "1. **چت هوش مصنوعی:** با لحن طنز و بامزه به هر سوالی پاسخ می‌دهم.\n"
        "2. **ثبت اصل من:** می‌توانید با ارسال `ثبت اصل من: نام، سن، شهر` مشخصات خود را ذخیره کنید.\n"
        "3. **مشاهده اصل:** با ارسال عبارت `اصل من` مشخصات ثبت شده خود را ببینید.\n"
        "4. **خوشامدگویی:** به اعضای جدید با یک پیام طنزآمیز خوشامد می‌گویم.\n"
        "5. **ضد لینک:** لینک‌های ارسالی را در گروه‌ها حذف می‌کنم (اگر مدیر باشم).\n"
        "6. **دانستنی خودکار:** هر یک ساعت یک دانستنی طنزآمیز به گروه‌های ثبت شده می‌فرستم.\n"
        "7. **ابزارهای گروهی:** از دستورات `/getgroupid` و `/admincheck` برای مدیریت گروه استفاده کنید.\n"
        "8. **وظایف:** با دستور `/tasks` همین لیست را مشاهده می‌کنید."
    )
    await update.message.reply_text(tasks_list, parse_mode='Markdown')

async def anti_link_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ["group", "supergroup"]:
        has_url_text = update.message.text and ('http://' in update.message.text or 'https://' in update.message.text or 'www.' in update.message.text)
        has_url_entity = update.message.entities and any(e.type in ['url', 'text_link'] for e in update.message.entities)
        
        if has_url_text or has_url_entity:
            try:
                await update.message.delete()
                print(f"Link message deleted from chat {update.effective_chat.id}")
            except Exception as e:
                print(f"Could not delete message (missing permission?): {e}")

async def greet_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot and member.username != context.bot.username:
            continue
        
        member_name = member.full_name
        
        if client:
            try:
                prompt = f"یک پیام خوش آمدگویی بسیار کوتاه و طنزآمیز برای کاربر جدید {member_name} که تازه به گروه پیوسته، بنویس و از او بخواه که برای ثبت مشخصات، عبارت 'ثبت اصل من:' را به همراه مشخصات خود (مثلا نام، سن، شهر) بفرستد. خودت را شیطون بلا معرفی کن."
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    config={"system_instruction": SYSTEM_INSTRUCTION}
                )
                welcome_text = response.text
            except Exception as e:
                print(f"Gemini welcome message generation failed: {e}")
                welcome_text = f"سلام {member_name}، به گروه خوش آمدید! (شیطون بلا در حال استراحت است) برای ثبت مشخصات، لطفاً پیام خود را با 'ثبت اصل من:' شروع کنید."
        else:
             welcome_text = f"سلام {member_name}، به گروه خوش آمدید! برای ثبت مشخصات، لطفاً پیام خود را با 'ثبت اصل من:' شروع کنید."

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text
        )

async def save_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    if message_text.lower().startswith("ثبت اصل من:"):
        user_info = message_text[len("ثبت اصل من:"):].strip()
        
        if len(user_info) < 5: 
            await update.message.reply_text("مشخصاتت کو؟ حداقل یه چیزی بنویس! (اصل من را با اطلاعات کامل بنویس)")
            return True
            
        USER_INFO[user_id] = user_info
        
        if client:
             try:
                prompt = f"به کاربر بگو مشخصاتش ('{user_info}') با موفقیت ثبت شد و بگو 'حالا برو حالشو ببر!' با لحن طنز و بامزه شیطون بلا."
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    config={"system_instruction": SYSTEM_INSTRUCTION}
                )
                reply_text = response.text
             except Exception:
                 reply_text = "ثبت شد! حالا برو حالشو ببر! 😉"
        else:
             reply_text = "ثبت شد! حالا برو حالشو ببر! 😉"

        await update.message.reply_text(reply_text)
        return True
    return False

async def show_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip().lower()
    
    if message_text in ["اصل من", "مشخصات من"]:
        if user_id in USER_INFO:
            info = USER_INFO[user_id]
            
            display_message = await update.message.reply_text(
                f"🎉 شیطون بلا، این هم اصل تو: 🎉\n\n**{info}**",
                parse_mode='Markdown'
            )
            
            await asyncio.sleep(3)
            try:
                await display_message.delete()
            except Exception as e:
                print(f"Could not delete message: {e}")
                
        else:
            await update.message.reply_text("ببخشید! شیطون بلا هنوز اصل شما را ثبت نکرده! ابتدا با 'ثبت اصل من:' مشخصاتت را بفرست.")
        return True
    return False

# --- قابلیت دانستنی خودکار (JobQueue) ---

async def send_fact_to_groups(context: CallbackContext):
    if not GROUP_IDS:
        print("GROUP_IDS is empty. Cannot send facts.")
        return
        
    if client is None:
        print("Gemini client is not available. Cannot generate fact.")
        return

    try:
        prompt = "یک دانستنی جالب، کوتاه و کمی طنز درباره حیوانات، فضا، یا تاریخ بنویس. این دانستنی باید به عنوان یک پیام گروهی جذاب و شیطنت آمیز از طرف شیطون بلا باشد. در انتها با یک شکلک بامزه پیام را تمام کن."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )
        fact_text = response.text
        
        for chat_id in GROUP_IDS:
            try:
                await context.bot.send_message(chat_id=chat_id, text=fact_text)
            except Exception as e:
                print(f"Failed to send message to chat {chat_id}: {e}")
                
    except Exception as e:
        print(f"Error generating or sending periodic fact: {e}")

# تابع /getgroupid: 
async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        chat_id = update.message.chat.id
        if chat_id not in GROUP_IDS:
            GROUP_IDS.append(chat_id)
            await update.message.reply_text(
                f"ID این گروه: `{chat_id}` با موفقیت به لیست ارسال دانستنی‌های شیطون بلا اضافه شد! (ID در حافظه موقت ربات ثبت شد)", 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"ID این گروه (`{chat_id}`) قبلاً در لیست ارسال دانستنی‌ها ثبت شده است.", 
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text("این دستور فقط در گروه‌ها کاربرد دارد.")

# تابع آماده سازی JobQueue (رفع خطای run_repeating)
async def post_init_job_queue(application: Application):
    """Adds the recurring job after the application is started."""
    if application.job_queue:
        # تنظیم ارسال دانستنی هر 3600 ثانیه (1 ساعت)
        application.job_queue.run_repeating(send_fact_to_groups, interval=3600, first=60)
        print("JobQueue: Periodic fact sending job added successfully.")

# --- تابع اصلی ---

def main():
    # ساخت اپلیکیشن با JobQueue
    application = Application.builder().token(TOKEN).post_init(post_init_job_queue).build()
    
    # 2. افزودن فیلترها و دستورات مدیریتی
    application.add_handler(CommandHandler("admincheck", admin_check))
    application.add_handler(CommandHandler("getgroupid", get_group_id))
    application.add_handler(CommandHandler("tasks", show_tasks)) 
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_members))
    
    # فیلتر ضد لینک
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, anti_link_filter), group=0) 
    
    # هوش مصنوعی
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat), group=1) # <-- هندلر ai_chat که قبلا کم بود
    
    if WEBHOOK_URL:
        # اجرای JobQueue و وب‌هوک در محیط Koyeb
        application.run_webhook(
            listen="0.0.0.0", 
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        print(f"Bot started with webhook at: {WEBHOOK_URL}/{TOKEN}")
    else:
        # اجرای JobQueue در حالت Polling (برای تست محلی - Termux)
        application.run_polling(poll_interval=3.0)
        print("Running with polling (local test)...") # پیام موفقیت برای Termux


if __name__ == '__main__':
    main()
