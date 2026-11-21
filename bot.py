
import os
import zipfile
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BASE_DIR = Path(__file__).parent
MATERIALS_DIR = BASE_DIR / "materials"

PAGE_SIZE = 10

CATEGORIES = {
    "slides": "Slides",
    "finals": "Finals",
    "midterm1": "Midterm1",
    "midterm2": "Midterm2",
    "syllabus": "Syllabus",
}


# ==================================================
# 2. COURSE AND DOCUMENT FUNCTIONS
# ==================================================

def get_course_folder(course):
    """Find a course folder safely."""

    if not course or Path(course).name != course:
        return None

    folder = MATERIALS_DIR / course

    if folder.is_dir():
        return folder

    return None


def get_documents(course, category):
    """Retrieve PDF documents from a category folder."""

    course_folder = get_course_folder(course)

    if course_folder is None:
        return []

    folder = course_folder / CATEGORIES[category]

    if not folder.is_dir():
        return []

    documents = [
        file for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".pdf"
        and not file.name.startswith(".")
    ]

    return sorted(documents, key=lambda file: file.name.casefold())


def create_browser(course, category, page):
    """Create a paginated document browser."""

    documents = get_documents(course, category)

    total = len(documents)

    total_pages = max(
        1,
        (total + PAGE_SIZE - 1) // PAGE_SIZE
    )

    page = max(0, min(page, total_pages - 1))

    start_index = page * PAGE_SIZE
    end_index = min(start_index + PAGE_SIZE, total)

    keyboard = []

    # Document buttons
    for index in range(start_index, end_index):

        document = documents[index]

        button_name = document.name

        if len(button_name) > 45:
            button_name = button_name[:42] + "..."

        keyboard.append([
            InlineKeyboardButton(
                f"📄 {button_name}",
                callback_data=f"f|{course}|{category}|{index}"
            )
        ])

    # Pagination buttons
    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Previous",
                callback_data=f"p|{course}|{category}|{page - 1}"
            )
        )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Next ➡️",
                callback_data=f"p|{course}|{category}|{page + 1}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    # ZIP download button
    if total > 1:
        keyboard.append([
            InlineKeyboardButton(
                "📦 Download all (ZIP)",
                callback_data=f"z|{course}|{category}"
            )
        ])

    text = (
        f"📚 {course} — {CATEGORIES[category]}\n\n"
        f"Found {total} PDF document(s).\n"
        f"Page {page + 1} of {total_pages}.\n\n"
        "Select a document to download:"
    )

    return text, InlineKeyboardMarkup(keyboard)


# ==================================================
# 3. BASIC TELEGRAM COMMANDS
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Hello! Welcome to AUA Academic Assistant! 🎓\n\n"
        "I can help you find university materials.\n\n"
        "Use /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 AVAILABLE COMMANDS\n\n"
        "/courses - List available courses\n"
        "/slides CS112 - Lecture slides\n"
        "/finals CS112 - Final exams\n"
        "/midterm1 CS112 - First midterm\n"
        "/midterm2 CS112 - Second midterm\n"
        "/syllabus CS112 - Course syllabus\n\n"
        "You can download individual PDFs or browse multiple documents."
    )


# ==================================================
# 4. COURSE LIST
# ==================================================

async def courses_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not MATERIALS_DIR.is_dir():

        await update.message.reply_text(
            "The materials folder does not exist."
        )

        return

    courses = sorted(
        [
            folder.name
            for folder in MATERIALS_DIR.iterdir()
            if folder.is_dir()
            and not folder.name.startswith(".")
        ],
        key=str.casefold
    )

    if not courses:

        await update.message.reply_text(
            "No courses have been added yet."
        )

        return

    message = "📚 AVAILABLE COURSES\n\n"

    for course in courses:
        message += f"• {course}\n"

    message += "\nExample: /slides CS112"

    await update.message.reply_text(message)


# ==================================================
# 5. AUTOMATIC DOCUMENT DELIVERY
# ==================================================

def make_category_handler(category):

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not context.args:

            await update.message.reply_text(
                f"Please specify a course.\n\n"
                f"Example: /{category} CS112"
            )

            return

        course = context.args[0]

        if get_course_folder(course) is None:

            await update.message.reply_text(
                f"Course '{course}' was not found.\n\n"
                "Use /courses to see available courses."
            )

            return

        documents = get_documents(course, category)

        # CASE 1: No documents
        if len(documents) == 0:

            await update.message.reply_text(
                f"No PDF documents found in "
                f"{course}/{CATEGORIES[category]}."
            )

        # CASE 2: Exactly one document
        elif len(documents) == 1:

            document = documents[0]

            try:

                with document.open("rb") as file:

                    await update.message.reply_document(
                        document=file,
                        filename=document.name,
                        caption=f"{course} — {CATEGORIES[category]}"
                    )

            except Exception as error:

                print(f"Document error: {error}")

                await update.message.reply_text(
                    "Sorry, I couldn't send this document."
                )

        # CASE 3: Multiple documents
        else:

            text, keyboard = create_browser(
                course,
                category,
                0
            )

            await update.message.reply_text(
                text,
                reply_markup=keyboard
            )

    return handler


# ==================================================
# 6. BUTTON INTERACTIONS
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data.split("|")

    action = data[0]
    course = data[1]
    category = data[2]

    if category not in CATEGORIES:

        await query.message.reply_text(
            "Invalid document category."
        )

        return

    if get_course_folder(course) is None:

        await query.message.reply_text(
            "Course folder not found."
        )

        return

    documents = get_documents(course, category)

    # ----------------------------------------------
    # PAGE NAVIGATION
    # ----------------------------------------------

    if action == "p":

        page = int(data[3])

        text, keyboard = create_browser(
            course,
            category,
            page
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard
        )

    # ----------------------------------------------
    # INDIVIDUAL DOCUMENT DOWNLOAD
    # ----------------------------------------------

    elif action == "f":

        index = int(data[3])

        if index < 0 or index >= len(documents):

            await query.message.reply_text(
                "This document is no longer available."
            )

            return

        document = documents[index]

        try:

            with document.open("rb") as file:

                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=file,
                    filename=document.name
                )

        except Exception as error:

            print(f"Document error: {error}")

            await query.message.reply_text(
                "Sorry, I couldn't send this document."
            )

    # ----------------------------------------------
    # DOWNLOAD ALL DOCUMENTS AS ZIP
    # ----------------------------------------------

    elif action == "z":

        if not documents:

            await query.message.reply_text(
                "There are no documents to download."
            )

            return

        try:

            with tempfile.TemporaryDirectory() as temp_dir:

                zip_path = Path(temp_dir) / (
                    f"{course}_{CATEGORIES[category]}.zip"
                )

                with zipfile.ZipFile(
                    zip_path,
                    "w",
                    zipfile.ZIP_DEFLATED
                ) as archive:

                    for document in documents:

                        archive.write(
                            document,
                            arcname=document.name
                        )

                with zip_path.open("rb") as file:

                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=file,
                        filename=zip_path.name,
                        caption=(
                            f"{course} — "
                            f"{CATEGORIES[category]}"
                        )
                    )

        except Exception as error:

            print(f"ZIP error: {error}")

            await query.message.reply_text(
                "Sorry, I couldn't create or send the ZIP."
            )


# ==================================================
# 7. MAIN PROGRAM
# ==================================================

def main():

    if not TOKEN:

        raise ValueError(
            "Telegram token not found in .env!"
        )

    app = Application.builder().token(TOKEN).build()

    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("courses", courses_command))

    # Document category commands
    for category in CATEGORIES:

        app.add_handler(
            CommandHandler(
                category,
                make_category_handler(category)
            )
        )

    # Interactive buttons
    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("AUA Academic Assistant is running!")

    app.run_polling()


if __name__ == "__main__":
    main()
