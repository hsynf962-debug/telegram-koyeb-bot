```python
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Your Bot Token
TOKEN = '7313799357:AAEX6lK-9zFhQwkclXmDo094MRY1dMDFr5E' 

# The server will set a PORT environment variable
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# 1. Define an asynchronous function to handle messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# 2. Main function to start the bot
def main():
    # 1. Create the Application
    application = Application.builder().token(TOKEN).build()

    # 2. Add the handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # 3. Start the Webhook
    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0", 
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        print(f"Bot started with webhook at: {WEBHOOK_URL}/{TOKEN}")
    else:
        # Fallback to polling (for local testing only)
        print("Running with polling (local test)...")
        application.run_polling(poll_interval=3.0)


if __name__ == '__main__':
    main()
```
