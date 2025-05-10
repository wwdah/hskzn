
import logging
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import smtplib
from email.mime.text import MIMEText

logging.basicConfig(level=logging.INFO)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل لي ملف accounts.txt الذي يحتوي على حسابات البريد.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document
    if document.file_name.endswith(".txt"):
        file = await document.get_file()
        file_path = await file.download_to_drive()
        
        with open(file_path, "r") as f:
            accounts = [line.strip().split(",") for line in f.readlines()]
        user_data[update.effective_user.id] = {"accounts": accounts}
        
        await update.message.reply_text("تم تحميل الحسابات. الآن أرسل الإعلان بهذا الشكل:\n\n/announce بريد_الزبون\nثم أرسل نص الإعلان.")
    else:
        await update.message.reply_text("الرجاء إرسال ملف بصيغة .txt فقط.")

async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("يرجى إرسال الأمر بهذا الشكل:\n/announce بريد_الزبون")
        return
    user_id = update.effective_user.id
    if user_id not in user_data or "accounts" not in user_data[user_id]:
        await update.message.reply_text("لم أستلم منك ملف الحسابات بعد.")
        return
    
    user_data[user_id]["target_email"] = context.args[0]
    user_data[user_id]["awaiting_message"] = True
    await update.message.reply_text("أرسل الآن نص الإعلان الترويجي.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and user_data[user_id].get("awaiting_message"):
        message = update.message.text
        target_email = user_data[user_id]["target_email"]
        accounts = user_data[user_id]["accounts"]
        await update.message.reply_text(f"جاري الإرسال من {len(accounts)} حسابًا...")

        successes = 0
        for email, password in accounts:
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(email, password)

                msg = MIMEText(message)
                msg["Subject"] = "برقيه عاجله لفريق الدعم "
                msg["From"] = email
                msg["To"] = target_email

                server.sendmail(email, target_email, msg.as_string())
                server.quit()
                successes += 1
            except Exception as e:
                print(f"خطأ عند الإرسال من {email}: {e}")

        await update.message.reply_text(f"تم الإرسال من {successes}/{len(accounts)} حسابًا.")
        user_data[user_id]["awaiting_message"] = False

if __name__ == "__main__":
    bot_token = "7637409754:AAHGHqx2s7VWzuYjVmJJ_r1QwB4EmV4KJng"
    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("announce", announce_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    print("البوت يعمل...")
    app.run_polling()
