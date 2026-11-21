## How It Works

AUA Academic Assistant is built around a simple idea: students should be able to access their academic materials directly through Telegram without manually searching through folders or asking others to send files.

The bot connects Telegram users to locally stored academic resources through an organized file system.

### 1. Course Detection

When the bot starts, it checks the `materials/` directory and identifies the available courses.

Each course is represented by its own folder. This means new courses can be added without modifying the bot's source code.

### 2. Resource Organization

Inside each course folder, materials are separated into predefined categories:

- `Slides/`
- `Midterm1/`
- `Midterm2/`
- `Finals/`
- `Syllabus/`

The bot uses this folder structure to determine which documents belong to each course and category.

### 3. Student Requests

Students interact with the bot using Telegram commands.

For example:

```text
/slides CS112
```

The bot interprets the request as:
- Resource category: Slides
- Course: CS112

It then searches the corresponding folder for PDF documents.

### 4. Document Retrieval

The bot checks how many PDF files are available and responds accordingly:

| Available PDFs | Bot response |
|---|---|
| 0 | Informs the student that no documents are available |
| 1 | Sends the PDF immediately |
| Multiple | Displays a selectable document list |

When multiple documents are available, students can navigate between pages and select individual files.

### 5. Download All

Students can also choose to download all available PDFs in a category.

The bot collects the documents, creates a ZIP archive, and sends it directly through Telegram.

### 6. Adding New Materials

The system is designed to make academic resource management straightforward.

To add new materials:
1. Open the appropriate course folder.
2. Select the relevant category.
3. Place the PDF file inside.

The bot automatically detects the new document the next time a student requests that category. No code changes or filename modifications are required.

---

## System Architecture

The project follows a straightforward request-and-response workflow:

```text
        STUDENT
           |
           v
     TELEGRAM BOT
           |
           v
    PROCESS COMMAND
           |
           v
  IDENTIFY COURSE & CATEGORY
           |
           v
   SEARCH MATERIALS FOLDER
           |
           v
    FIND AVAILABLE PDFs
           |
           v
     SELECT RESPONSE
       /    |     \
      /     |      \
    None   One   Multiple
     |      |       |
     v      v       v
   Notify  Send   Show Document
           PDF      Menu
                     |
                     v
               Student Selects
                     |
                     v
                 Send PDF
```

The main components are:

- **Telegram Interface:** Receives commands and delivers documents to students.
- **Bot Logic (`bot.py`):** Processes requests, identifies courses and categories, and controls document retrieval.
- **Materials Directory:** Stores course-specific academic resources in an organized folder structure.
- **Environment Configuration (`.env`):** Keeps the Telegram bot token separate from the source code.

