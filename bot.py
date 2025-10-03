import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
# کتابخانه جدید برای اتصال به هوش مصنوعی
from openai import OpenAI 

# Your Bot Token (توکن اصلی ربات شما)
TOKEN = '7313799357:AAEX6lK-9zFhQwkclXmDo094MRY1dMDFr5E' 

# Initialize the OpenAI client. 
# این بخش به صورت خودکار به دنبال کلید در متغیر محیطی OPENAI_API_KEY در Koyeb می‌گردد
try:
    client = OpenAI()
except Exception as e:
    print(f"OpenAI Client Initialization Error: {e}")
    client = None


# متغیرهای محیطی Koyeb
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# 1. تابع اصلی برای پردازش پیام‌ها و ارسال به هوش مصنوعی
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگر پیام یک دستور باشد (مثل /start)، نادیده گرفته می‌شود
    if update.message.text.startswith('/'):
        return
    
    user_text = update.message.text
    
    # اگر اتصال به OpenAI برقرار نشد (یعنی کلید در Koyeb تنظیم نشده)
    if client is None:
        await update.message.reply_text("متأسفم، اتصال به سرویس هوش مصنوعی برقرار نشد. لطفاً کلید API را در تنظیمات Koyeb بررسی کنید.")
        return

    try:
        # 1. نمایش وضعیت 'در حال تایپ'
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        # 2. ارسال درخواست به مدل gpt-3.5-turbo 
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک دستیار هوش مصنوعی مفید و صمیمی هستید. به فارسی و مودبانه پاسخ دهید."},
                {"role": "user", "content": user_text}
            ]
        )
        
        # 3. استخراج پاسخ
        reply_text = response.choices[0].message.content
        
    except Exception as e:
        # مدیریت خطا
        reply_text = f"خطا در پردازش درخواست توسط هوش مصنوعی: {e}"
        print(f"API Error: {e}")

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
        # این حالت برای Koyeb اجرا نمی‌شود
        print("Running with polling (local test)...")
        application.run_polling(poll_interval=3.0)


if __name__ == '__main__':
    main()
