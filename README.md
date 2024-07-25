# Complaints-Suggestions python bot

This is a python telegram bot example for a simple complaint and suggestions that uses the [python-telegram-bot](https://python-telegram-bot.org) library.

## Overview

This Python script defines a Telegram bot designed to collect complaints and suggestions from users. It utilizes the `python-telegram-bot` library to interact with the Telegram API, `dotenv` for environment variable management, and `smtplib` along with `email.mime.text.MIMEText` for sending emails.

## Environment Variables

The bot requires the following environment variables to be set in a `.env` file:

- `MY_EMAIL`: The email address from which the bot sends summaries of complaints and suggestions.
- `ADMIN_EMAIL`: The email address to which the bot sends summaries of complaints and suggestions.
- `SERVER_APP_PASSWORD`: The app-specific password for the email server.
- `TOKE`: Telegram bot token.

## Dependencies

- `python-telegram-bot`: For Telegram bot functionality.
- `python-dotenv`: For loading environment variables from a `.env` file.
- `aiofiles`: For asynchronous file operations (not explicitly used in the provided code but likely intended for async file handling).
- `smtplib`, `email.mime.text`: For sending emails.

## Main Components

### Decorators

- `@first_id_check`: A decorator to check and store the first message ID in a conversation with the bot. This is intended to track the start of interactions with each user.

### Commands

- `/start`: Greets the user and provides basic information about the bot.
- `/help`: Provides instructions on how to use the bot.
- `/complaint`: Initiates the process for submitting a complaint.
- `/suggestion`: Initiates the process for submitting a suggestion.
- `/cancel`: Cancels the current operation.
- `/clear`: Clears the current session data.

### Handlers

- `handle_text`: Handles generic text messages that are not commands.
- `handle_complaint`: Processes complaints.
- `handle_suggestion`: Processes suggestions.
- `handle_confirmation`: Handles confirmation messages from users.

### Jobs

- `send_cs`: Scheduled to run weekly, this job compiles and sends an email with all collected complaints and suggestions.
- `set_file_name`: Changes the file name to reflect the current week, intended for organizing submissions by week.

### Main Function

- `main()`: Sets up the bot, including command handlers and job scheduling.

## Running the Bot

To run the bot, ensure all dependencies are installed and environment variables are set in a `.env` file, then execute the script:

```bash
python main.py