import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, ConversationHandler

from dotenv import dotenv_values
from datetime import date, timedelta, time, timezone
import aiofiles
from os import path

import smtplib
from email.mime.text import MIMEText


# Import environment variables
config: dict[str, str] = {k: v for k, v in dotenv_values(".env").items() if v is not None}

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

WAITING_FOR_CS, CONFIRMATION = range(2)

FILE_NAME: str = ''
OLD_FILE_NAME: str = ''

# Decorators
def first_id_check(func):
    async def wrapper(update, context, *args, **kwargs):
        try:
            context.user_data["message_id_first"]
        except KeyError:
            context.user_data["message_id_first"] = update.message.message_id
        return await func(update, context, *args, **kwargs)
    return wrapper


# Commands
@first_id_check
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text('Hi! I am a bot designed to help you with your complaints and suggestions. Please type /help to see what I can do for you.')
    return ConversationHandler.END

@first_id_check
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text('I can help you with your complaints and suggestions.\nPlease type /complaint or /suggestion to start.\nThen write a suggestion or complaint and I will ask you to confirm.\nPlease write in English for anonymity.')
    return ConversationHandler.END

@first_id_check
async def complaint_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text('Please send your complaint.')
    return WAITING_FOR_CS

@first_id_check
async def suggestion_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text('Please send your suggestion.')
    return WAITING_FOR_CS

@first_id_check
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    await update.message.reply_text('Action canceled.')
    return ConversationHandler.END

@first_id_check
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message is not None
    assert context.user_data is not None

    first = context.user_data["message_id_first"]
    last: int = update.message.message_id
    message_ids = list(range(first, last + 1))
    await context.bot.delete_messages(chat_id=update.message.chat_id, message_ids=message_ids)
    context.user_data["message_id_first"] = last + 1
    return ConversationHandler.END


# Handlers
@first_id_check
async def handle_text(update: Update, context: CallbackContext) -> None:
    pass

@first_id_check
async def handle_complaint(update: Update, context: CallbackContext) -> int:
    assert update.message is not None
    assert context.user_data is not None

    context.user_data['user_message'] = f"Complaint: {update.message.text}"
    await update.message.reply_text(f'Received your complaint: "{update.message.text}".\n\nType "yes" to confirm. Anything else to cancel.')
    return CONFIRMATION

@first_id_check
async def handle_suggestion(update: Update, context: CallbackContext) -> int:
    assert update.message is not None
    assert context.user_data is not None

    context.user_data['user_message'] = f"Suggestion: {update.message.text}"
    await update.message.reply_text(f'Received your suggestion: "{update.message.text}".\n\nType "yes" to confirm. Anything else to cancel.')
    return CONFIRMATION

@first_id_check
async def handle_confirmation(update: Update, context: CallbackContext) -> int:
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    global FILE_NAME

    user_confirmation: str = update.message.text
    if user_confirmation.lower() == 'yes':
        async with aiofiles.open(path.join("data", FILE_NAME), 'a') as file:
            await file.write(f"{context.user_data['user_message']}\n\n")
        await update.message.reply_text('Thank you for your feedback. Please use /clear to delete your messages.')
    else:
        await update.message.reply_text('Message was not saved.')
    context.user_data['user_message'] = None
    return ConversationHandler.END


# Jobs
# Run job every week at 10:00 on Monday
async def send_cs(context: CallbackContext) -> None:
    assert context.job is not None

    # Get file content, ignore if file does not exist (first time)
    file_content: str = ''
    try:
        with open(f"data/{context.job.data}", 'r') as file:
            file_content = file.read()
    except IsADirectoryError:
        logger.warning(f"File does not exits. Ignore if file was not created since no complaints or suggestions were made.")
    logger.info(f"SENDING FILE CONTENT: {file_content}")

    # Send email
    msg = MIMEText(file_content)
    msg['Subject'] = f"Complaints and Suggestions for week {context.job.data}"
    msg['From'] = config['MY_EMAIL']
    #! msg['To'] = config['ADMIN_EMAIL1']
    #! msg['Cc'] = config['ADMIN_EMAIL2']
    msg['To'] = config['MY_EMAIL']
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(config['MY_EMAIL'], config['SERVER_APP_PASSWORD'])
    server.send_message(msg)
    server.quit()

# Change file name to current week each monday at 00:00
async def set_file_name(application) -> None:
    global FILE_NAME
    global OLD_FILE_NAME

    OLD_FILE_NAME = FILE_NAME
    current_date = date.today()
    monday = (current_date - timedelta(days = current_date.weekday()))
    date_shift = (monday + timedelta(days=6))
    FILE_NAME = f"C&S_{monday.strftime('%d-%m-%Y')}_{date_shift.strftime('%d-%m-%Y')}.txt"
    logger.info(f"CURRENT FILE NAME: {FILE_NAME}")


# Main
def main() -> None:
    global FILE_NAME
    global OLD_FILE_NAME

    app = Application.builder().token(config['TOKEN']).build()
    assert app.job_queue is not None

    # Create the ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('complaint', complaint_command), CommandHandler('suggestion', suggestion_command), CommandHandler('start', start_command), CommandHandler('help', help_command), CommandHandler('clear', clear_command)],
        states={
            WAITING_FOR_CS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint),MessageHandler(filters.TEXT & ~filters.COMMAND, handle_suggestion)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
    )

    # Schedule the job every week
    app.job_queue.run_daily(days=(1,), time=time(0, 0, 0, tzinfo=timezone(timedelta(seconds=10800))), callback=set_file_name, name='set_file_name')
    app.job_queue.run_daily(days=(1,), time=time(10, 0, 0, tzinfo=timezone(timedelta(seconds=10800))), callback=send_cs, name='send_cs', data=OLD_FILE_NAME)

    # Add the ConversationHandler to the dispatcher
    app.add_handler(conv_handler)
    # Handle any other non related messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Set initial file name
    app.post_init = set_file_name
    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)

# Run the main function if the script is executed directly
if __name__ == '__main__':
    # Run main function
    main()