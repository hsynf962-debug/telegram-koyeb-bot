import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
# کتابخانه جدید برای اتصال به هوش مصنوعی (Google GenAI)
from google import genai 
from google.genai.errors import APIError

# Your Bot Token
TOKEN = '7313799357:AAEX6lK-9zFhQwkclXmDo094MRY1dMDFr5E' 

# Initialize the Gemini client. 
# این بخش به صورت خودکار به دنبال کلید در متغیر محیطی GEMINI_API_KEY می‌گردد
try:
    # client = genai.Client() # این روش برای برخی از محیط‌ها کار نمی‌کند
    # از این روش برای اطمینان از خواندن کلید از متغیر محیطی استفاده می‌کنیم
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Gemini Client Initialization Error: {e}")
    client = None


# متغیرهای محیطی Koyeb
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# 1. تابع اصلی برای پردازش پیام‌ها و ارسال به هوش مصنوعی
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'):
        return
    
    user_text = update.message.text
    
    if client is None:
        await update.message.reply_text("متأسفم، اتصال به سرویس هوش مصنوعی برقرار نشد. لطفاً کلید GEMINI API را در تنظیمات Koyeb بررسی کنید.")
        return

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        # 2. ارسال درخواست به مدل Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # مدل سریع و کارآمد برای چت
            contents=[
                user_text
            ]
        )
        
        # 3. استخراج پاسخ
        reply_text = response.text
        
    except APIError as e:
        reply_text = f"خطا در پردازش درخواست توسط هوش مصنوعی (Gemini API): {e}"
        print(f"API Error: {e}")
    except Exception as e:
        reply_text = f"خطا در پردازش: {e}"
        print(f"General Error: {e}")

    # 4. ارسال پاسخ نهایی
    await update.message.reply_text(reply_text)

# 2. تابع اصلی برای شروع ربات
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))
    
    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0", 
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        print(f"Bot started with webhook at: {WEBHOOK_URL}/{TOKEN}")
    else:
        print("Running with polling (local test)...")
        application.run_polling(poll_interval=3.0)


if __name__ == '__main__':
    main()
