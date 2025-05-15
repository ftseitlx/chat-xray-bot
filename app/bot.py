import asyncio
import logging
import sys
import os
from datetime import datetime

import sentry_sdk
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand, Message, FSInputFile, 
    InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import re
from bs4 import BeautifulSoup
from aiogram.client.default import DefaultBotProperties
from pathlib import Path

from app.config import settings
from app.utils import cleanup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# Add a distinctive log message to verify this version is running
logger.info("========================================")
logger.info("TIMEOUT FIX VERSION 2025-05-14-001 ACTIVATED")
logger.info("REDEPLOYMENT FIX - TIMEOUT ERROR RESOLUTION")
logger.info("This version includes fixes for the timeout context manager error")
logger.info("========================================")

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
    )

# We'll instantiate the Bot later, after setting up the event loop (see __main__ block)
bot: Bot | None = None
dp = Dispatcher(storage=MemoryStorage())

# Setup main router
main_router = Router()


# Helper function to safely send messages in a task
async def safe_send_message(message: Message, text: str, **kwargs):
    """Send a Telegram message with basic retry logic (no extra tasks)."""
    try:
        return await message.answer(text, **kwargs)
    except Exception as e:
        logger.warning(f"safe_send_message error: {e} – retrying once")
        await asyncio.sleep(0.5)
        try:
            return await message.answer(text, **kwargs)
        except Exception as e2:
            logger.error(f"safe_send_message failed again: {e2}")
            return None


# Helper function to safely delete a message
async def safe_delete_message(message: Message):
    """Delete a Telegram message with basic error handling."""
    if message is None:
        return
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"safe_delete_message error: {e}")


@main_router.message(CommandStart())
async def command_start(message: Message):
    await safe_send_message(
        message,
        f"👋 Добро пожаловать в Chat X-Ray Bot, {message.from_user.first_name}!\n\n"
        f"Я могу проанализировать историю вашего общения и предоставить психологический анализ ваших отношений.\n\n"
        f"Просто отправьте мне файл экспорта чата (в формате .txt или .html, до 2 МБ), и я проведу глубокий анализ для вас.\n\n"
        f"Я использую передовые методы психологии, основанные на работах Габора Мате, Джона Готтмана и других исследователей отношений.\n\n"
        f"<b>Команды</b>:\n"
        f"/start - Показать это приветственное сообщение\n"
        f"/privacy - Просмотреть нашу политику конфиденциальности\n"
        f"/help - Показать справочную информацию\n"
        f"/about - Узнать о психологических теориях, используемых в анализе"
    )


@main_router.message(Command("privacy"))
async def privacy_command(message: Message):
    with open("docs/privacy_policy.md", "r") as f:
        privacy_text = f.read()
    
    await safe_send_message(
        message,
        "Наша Политика Конфиденциальности:\n\n"
        f"{privacy_text[:3900]}...\n\n"  # Limit to Telegram's message size
        "Для получения полной информации посетите наш веб-сайт."
    )


@main_router.message(Command("help"))
async def help_command(message: Message):
    await safe_send_message(
        message,
        "<b>Как использовать Chat X-Ray:</b>\n\n"
        "1. Экспортируйте историю чата из вашего мессенджера в текстовый файл (.txt) или HTML-файл (.html)\n"
        "2. Отправьте файл этому боту (размер файла должен быть не более 2 МБ)\n"
        "3. Дождитесь завершения анализа (обычно занимает около минуты благодаря параллельной обработке)\n"
        "4. Получите краткие выводы прямо в Telegram и ссылку на полный PDF-отчет\n\n"
        "<b>Поддерживаемые форматы:</b>\n"
        "• Текстовый экспорт WhatsApp\n"
        "• HTML-экспорт WhatsApp\n"
        "• Стандартные текстовые логи чатов\n\n"
        "<b>Примечания:</b>\n"
        "• Ваши загруженные файлы автоматически удаляются через 1 час\n"
        "• Отчеты доступны в течение 72 часов\n"
        "• В целях конфиденциальности мы не храним ваши данные чата на постоянной основе"
    )


@main_router.message(Command("about"))
async def about_command(message: Message):
    """Handle the /about command"""
    await safe_send_message(
        message,
        "<b>О психологическом анализе Chat X-Ray:</b>\n\n"
        "Наш анализ основан на нескольких ключевых психологических теориях:\n\n"
        "1. <b>Теория привязанности Габора Мате</b> - анализ моделей привязанности и их влияния на общение\n\n"
        "2. <b>Четыре всадника отношений Джона Готтмана</b> - выявление критики, защиты, презрения и игнорирования\n\n"
        "3. <b>Ненасильственное общение Маршалла Розенберга</b> - анализ потребностей, эмоций и запросов\n\n"
        "4. <b>Трансактный анализ Эрика Берна</b> - определение паттернов коммуникации Родитель-Взрослый-Ребенок\n\n"
        "Каждый отчет включает визуализацию данных, цитаты, анализ динамики отношений и конкретные рекомендации, основанные на этих психологических моделях."
    )


# Add a simple echo handler to test basic functionality
@main_router.message(F.text)
async def echo_message(message: Message):
    """Simple echo handler to test basic functionality"""
    logger.info(f"Received text message from user {message.from_user.id}: {message.text[:20]}...")
    
    # Only respond to direct messages, not commands
    if message.text.startswith('/'):
        return
        
    await safe_send_message(
        message,
        f"✓ Я получил ваше сообщение:\n\n"
        f"\"{message.text}\"\n\n"
        f"Для анализа чата, пожалуйста, отправьте файл с историей переписки (.txt или .html)."
    )
    logger.info(f"Echo response sent to user {message.from_user.id}")


# Define the FSM states
class ChatProcessingStates(StatesGroup):
    waiting_for_file = State()
    processing = State()


# Router for file handling
upload_router = Router()


# Function to extract key insights from HTML report for Telegram
async def extract_insights_for_telegram(html_content: str) -> str:
    """Extract key insights from HTML report for Telegram message"""
    # Using BeautifulSoup to parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize a result string with header
    insights = "<b>🔍 Краткий анализ отношений:</b>\n\n"
    
    # Try to get the main insights
    try:
        # Extract overview section (first paragraph)
        overview = soup.find('h2', text=re.compile('Общий обзор', re.IGNORECASE))
        if overview and overview.find_next('p'):
            first_paragraph = overview.find_next('p').text.strip()
            insights += f"<b>Общий обзор:</b> {first_paragraph[:200]}...\n\n"
        
        # Extract communication patterns
        patterns = soup.find('h2', text=re.compile('Паттерны общения', re.IGNORECASE))
        if patterns and patterns.find_next('p'):
            pattern_text = patterns.find_next('p').text.strip()
            insights += f"<b>Паттерны общения:</b> {pattern_text[:200]}...\n\n"
        
        # Extract emotional analysis
        emotions = soup.find('h2', text=re.compile('Анализ эмоций', re.IGNORECASE))
        if emotions and emotions.find_next('p'):
            emotion_text = emotions.find_next('p').text.strip()
            insights += f"<b>Эмоциональный анализ:</b> {emotion_text[:200]}...\n\n"
        
        # Extract top recommendations (first 3)
        recommendations = soup.find('h2', text=re.compile('Рекомендации', re.IGNORECASE))
        if recommendations:
            rec_items = recommendations.find_next_siblings('div', class_='recommendation')[:3]
            if rec_items:
                insights += "<b>Ключевые рекомендации:</b>\n"
                for i, rec in enumerate(rec_items, 1):
                    rec_text = rec.text.strip()
                    insights += f"{i}. {rec_text[:100]}...\n"
        
        # Extract key quotes (first 2)
        quotes = soup.find_all('div', class_='quote')[:2]
        if quotes:
            insights += "\n<b>Ключевые цитаты:</b>\n"
            for quote in quotes:
                quote_text = quote.find('p').text.strip()
                author = quote.find('p', class_='quote-author')
                if author:
                    insights += f"• <i>«{quote_text}»</i> — {author.text.strip()}\n"
                else:
                    insights += f"• <i>«{quote_text}»</i>\n"
    
    except Exception as e:
        logger.error(f"Error extracting insights: {e}")
        insights += "Не удалось извлечь подробные выводы. Пожалуйста, обратитесь к полному отчету."
    
    return insights


# Helper function to safely edit a message
async def safe_edit_message(message: Message, text: str, **kwargs):
    try:
        return await message.edit_text(text, **kwargs)
    except Exception as e:
        logger.warning(f"safe_edit_message error: {e} – retrying once")
        await asyncio.sleep(0.5)
        try:
            return await message.edit_text(text, **kwargs)
        except Exception as e2:
            logger.error(f"safe_edit_message failed again: {e2}")
            return None


@upload_router.message(F.document)
async def handle_document(message: Message):
    """Handle document uploads and process valid text or HTML files"""
    logger.info(f"[TIMEOUT-FIX] Document handler started for user {message.from_user.id}: {getattr(message.document, 'file_name', 'Unknown')}")
    
    # Check if document exists
    if not message.document:
        logger.warning(f"[TIMEOUT-FIX] Document not found in message from user {message.from_user.id}")
        await safe_send_message(message, "⚠️ Документ не найден. Пожалуйста, отправьте текстовый файл или HTML-экспорт чата.")
        return
    
    # Log document details
    logger.info(f"[TIMEOUT-FIX] Document details: name={message.document.file_name}, size={message.document.file_size}, mime={message.document.mime_type}")
    
    # Check MIME type or fallback to file extension for Telegram exports, which often lack correct MIME
    valid_mime_types = ["text/plain", "text/html", "application/octet-stream"]
    valid_extensions = [".txt", ".html", ".htm"]

    file_extension = Path(message.document.file_name or "").suffix.lower()

    if (message.document.mime_type not in valid_mime_types) and (file_extension not in valid_extensions):
        logger.warning(
            f"[TIMEOUT-FIX] Invalid file type: mime={message.document.mime_type}, ext={file_extension} from user {message.from_user.id}"
        )
        await safe_send_message(
            message,
            "⚠️ Неверный формат файла. Пожалуйста, отправьте текстовый файл (.txt) или HTML-экспорт чата (.html)."
        )
        return
    
    # Check file size
    if message.document.file_size > settings.MAX_FILE_SIZE:
        logger.warning(f"[TIMEOUT-FIX] File too large: {message.document.file_size} bytes from user {message.from_user.id}")
        await safe_send_message(
            message,
            f"⚠️ Файл слишком большой. Максимальный размер {settings.MAX_FILE_SIZE // (1024 * 1024)} МБ."
        )
        return
    
    # All checks passed, let's download and process the file
    logger.info(f"[TIMEOUT-FIX] File validation passed, proceeding to download and process file from user {message.from_user.id}")
    
    try:
        # Send acknowledgment message - THIS USED TO FAIL WITH TIMEOUT ERROR
        logger.info("[TIMEOUT-FIX] About to send acknowledgment message using safe_send_message")
        ack_message = await safe_send_message(message, "✅ Ваш файл получен. Начинаю анализ...")
        logger.info("[TIMEOUT-FIX] Acknowledgment message sent successfully")
        
        # Process the file by importing here to avoid circular imports
        from app.services.chunker import split_chat
        from app.services.llm_primary import process_chunks
        from app.services.llm_meta import generate_meta_report
        from app.services.render import render_to_pdf
        from app.utils.logging_utils import log_cost
        import uuid
        import openai
        
        # Generate unique IDs for the files
        file_id = str(uuid.uuid4())
        logger.info(f"Generated file ID: {file_id}")
        
        # Set the appropriate file extension based on mime type
        file_extension = ".html" if message.document.mime_type == "text/html" else ".txt"
        upload_file_path = settings.UPLOAD_DIR / f"{file_id}{file_extension}"
        report_file_path = settings.REPORT_DIR / f"{file_id}.pdf"
        html_file_path = settings.REPORT_DIR / f"{file_id}_report.html"
        
        logger.info(f"File paths: upload={upload_file_path}, report={report_file_path}, html={html_file_path}")
        
        # Download the file
        logger.info("Starting file download")
        try:
            file_path = await bot.download(message.document, destination=upload_file_path)
            logger.info(f"File downloaded successfully to {file_path}")
            
            # Verify file was downloaded correctly
            if os.path.exists(upload_file_path):
                file_size = os.path.getsize(upload_file_path)
                logger.info(f"Downloaded file size: {file_size} bytes")
                if file_size == 0:
                    logger.error("Downloaded file is empty")
                    await safe_send_message(message, "❌ Ошибка: загруженный файл пуст. Пожалуйста, проверьте файл и попробуйте снова.")
                    return
            else:
                logger.error(f"File not found after download: {upload_file_path}")
                await safe_send_message(message, "❌ Ошибка при сохранении файла. Пожалуйста, попробуйте снова.")
                return
        except Exception as download_error:
            logger.exception(f"Error downloading file: {download_error}")
            await safe_send_message(message, "❌ Ошибка при загрузке файла. Пожалуйста, попробуйте снова.")
            return
        
        # Let the user know we're processing and all data is anonymized
        logger.info("Sending status message")
        status_message = await safe_send_message(
            message,
            "🔍 <b>Анализирую чат...</b>\n\n"
            "⚠️ <b>Важно:</b> Все личные данные в чате анонимизируются при обработке. "
            "Имена заменяются общими идентификаторами, а чувствительная информация не сохраняется. "
            "Ваша конфиденциальность важна для нас.\n\n"
            "Это может занять минуту или две."
        )
        
        # Split the chat into chunks
        logger.info(f"Splitting chat from file {upload_file_path}")
        chunks = split_chat(upload_file_path)
        num_chunks = len(chunks)
        logger.info(f"Split chat into {num_chunks} chunks")
        
        if num_chunks == 0:
            logger.warning(f"No chunks extracted from file {upload_file_path}")
            await safe_send_message(message, "⚠️ Не удалось обработать файл. Возможно, он пуст или имеет неправильный формат?")
            os.unlink(upload_file_path)
            return
        
        # Progress bar helper
        def _build_progress_bar(done: int, total: int, bar_len: int = 20) -> str:
            """Return a unicode progress bar string."""
            filled = int(bar_len * done / total) if total else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            return f"[{bar}] {done}/{total}"

        # Initial progress message
        await safe_edit_message(
            status_message,
            f"🔄 <b>Обрабатываю фрагменты данных чата</b> 0/{num_chunks}\n{_build_progress_bar(0, num_chunks)}",
            parse_mode=ParseMode.HTML,
        )

        # Throttle progress updates to avoid Telegram flood & race conditions
        progress_lock = asyncio.Lock()
        _last_update_ts: float = 0.0  # nonlocal for closure

        async def _progress_callback(done: int, total: int):
            nonlocal _last_update_ts
            # Update no more than once per second
            now = asyncio.get_event_loop().time()
            if now - _last_update_ts < 1:
                return
            _last_update_ts = now

            async with progress_lock:
                await safe_edit_message(
                    status_message,
                    f"🔄 <b>Обрабатываю фрагменты данных чата</b> {done}/{total}\n{_build_progress_bar(done, total)}",
                    parse_mode=ParseMode.HTML,
                )

        analysis_results, primary_tokens = await process_chunks(chunks, progress_callback=_progress_callback)
        logger.info(f"Successfully processed {len(analysis_results)} chunk results")
        
        # Generate meta report with GPT-4
        logger.info(f"Starting meta report generation with {settings.META_MODEL}")
        await safe_edit_message(status_message, "✨ Создаю психологические выводы и генерирую отчет...")
        
        try:
            total_messages = sum(len(chunk) for chunk in chunks)
            html_content, meta_tokens = await generate_meta_report(analysis_results, total_messages)
            logger.info("Successfully generated meta report HTML content")
            
            # Save HTML content to file
            logger.info(f"Saving HTML content to {html_file_path}")
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Render HTML to PDF
            logger.info(f"Rendering HTML to PDF at {report_file_path}")
            pdf_url = await render_to_pdf(html_file_path, report_file_path)
            
            # Generate a public URL for the PDF
            report_url = f"{settings.WEBHOOK_HOST}/reports/{os.path.basename(report_file_path)}" if settings.WEBHOOK_HOST else f"file://{report_file_path}"
            logger.info(f"Report URL: {report_url}")
            
            # Calculate and log approximate cost
            approx_cost = (primary_tokens * settings.GPT35_COST_PER_TOKEN) + (meta_tokens * settings.GPT4_TURBO_COST_PER_TOKEN)
            await log_cost(message.from_user.id, num_chunks, approx_cost)
            
            # Extract insights for Telegram message
            logger.info("Extracting insights for Telegram message")
            telegram_insights = await extract_insights_for_telegram(html_content)
            
            # Send success message with download option
            
            # If we're in local mode without a webhook, just send the file directly
            if not settings.WEBHOOK_HOST:
                logger.info("Running in local mode, sending file directly")
                await safe_delete_message(status_message)
                
                # First send insights as HTML message
                logger.info("Sending insights message")
                await safe_send_message(
                    message,
                    telegram_insights,
                    parse_mode=ParseMode.HTML
                )
                
                # Then send the full report as a document
                logger.info("Sending report document")
                await safe_send_message(
                    message,
                    "Отправляю полный отчет..."
                )
                
                # Use safe task for document sending
                async def _send_document():
                    logger.info("[TIMEOUT-FIX] Inside _send_document task")
                    try:
                        result = await message.answer_document(
                            FSInputFile(report_file_path),
                            caption="Ваш полный отчет Chat X-Ray готов. Этот файл будет доступен в течение 72 часов."
                        )
                        logger.info("[TIMEOUT-FIX] Document sent successfully")
                        return result
                    except Exception as inner_e:
                        logger.error(f"[TIMEOUT-FIX] Error in document sending task: {inner_e}")
                        return None
                
                logger.info("[TIMEOUT-FIX] Creating task for document sending")
                await asyncio.create_task(_send_document())
                logger.info("[TIMEOUT-FIX] Document sending task completed")
            else:
                # In production with webhook, send insights and a link
                logger.info("Running in webhook mode, sending link to report")
                await safe_delete_message(status_message)
                
                # First send insights as HTML message
                logger.info("Sending insights message")
                await safe_send_message(
                    message,
                    telegram_insights,
                    parse_mode=ParseMode.HTML
                )
                
                # Then send the link to full report
                logger.info("Creating download button with URL")
                download_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text="📊 Скачать полный отчет",
                            url=report_url
                        )]
                    ]
                )
                
                logger.info("Sending download button message")
                await safe_send_message(
                    message,
                    "📋 Для получения полного отчета нажмите на кнопку ниже:",
                    reply_markup=download_markup
                )
            
            # Add metadata to track file expiration
            logger.info("Adding file expiration metadata")
            expiration_time = datetime.now().timestamp() + (settings.REPORT_RETENTION_HOURS * 3600)
            with open(f"{report_file_path}.meta", "w") as f:
                f.write(str(expiration_time))
            
            # Delete the original upload file metadata
            upload_expiration_time = datetime.now().timestamp() + (settings.UPLOAD_RETENTION_HOURS * 3600)
            with open(f"{upload_file_path}.meta", "w") as f:
                f.write(str(upload_expiration_time))
            
            logger.info(f"Successfully completed processing file for user {message.from_user.id}")
            
        except openai.RateLimitError as e:
            logger.error(f"Rate limit error during meta analysis: {e}")
            await safe_edit_message(
                status_message,
                "⚠️ Мы достигли ограничения запросов при создании отчета.\n\n"
                "Это обычно происходит при обработке очень больших чатов или в периоды пиковой нагрузки.\n\n"
                "Пожалуйста, попробуйте загрузить файл меньшего размера или повторите попытку через несколько минут."
            )
            
        except Exception as e:
            logger.exception(f"Error in meta analysis: {e}")
            await safe_edit_message(
                status_message,
                "❌ Произошла ошибка при создании отчета.\n\n"
                f"Детали ошибки: {str(e)}\n\n"
                "Пожалуйста, попробуйте еще раз или обратитесь в поддержку, если проблема не исчезнет."
            )
            
    except Exception as e:
        logger.exception(f"Error processing file: {e}")
        if settings.SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        
        await safe_send_message(
            message,
            "❌ Извините, произошла ошибка при обработке вашего файла. Пожалуйста, попробуйте позже."
        )
        
        # Make sure to clean up any files if there was an error
        if 'upload_file_path' in locals() and os.path.exists(upload_file_path):
            try:
                os.unlink(upload_file_path)
                logger.info(f"Cleaned up upload file after error: {upload_file_path}")
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up file: {cleanup_error}")


# Health check endpoint
async def health_check(request):
    logger.info("Health check request received")
    return web.Response(text="OK", status=200)


async def main():
    """Entry-point coroutine.
    Sets up dispatcher, bot, scheduler and either starts webhook-based aiohttp
    application or long-polling depending on environment variables."""

    global bot  # we assigned a forward declaration at module level

    # -------------------------------------------------
    # 1. Create Bot *inside* the running event-loop
    # -------------------------------------------------
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # -------------------------------------------------
    # 2. Register routers
    # -------------------------------------------------
    dp.include_router(main_router)
    dp.include_router(upload_router)

    # -------------------------------------------------
    # 3. Start background scheduler for cleanup
    # -------------------------------------------------
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        cleanup.clean_old_uploads,
        "interval",
        hours=1,
        kwargs={"hours": settings.UPLOAD_RETENTION_HOURS},
    )
    scheduler.add_job(
        cleanup.clean_old_reports,
        "interval",
        hours=6,
        kwargs={"hours": settings.REPORT_RETENTION_HOURS},
    )
    scheduler.start()

    # -------------------------------------------------
    # 4. Determine operation mode (webhook vs polling)
    # -------------------------------------------------
    is_webhook_mode = bool(
        settings.WEBHOOK_URL or os.environ.get("PORT") or os.environ.get("RENDER_EXTERNAL_URL")
    )

    logger.info(f"Bot startup mode: {'webhook' if is_webhook_mode else 'polling'}")

    # Build/adjust webhook URL dynamically when running on Render.com
    if is_webhook_mode and not settings.WEBHOOK_URL and os.environ.get("RENDER_EXTERNAL_URL"):
        settings.WEBHOOK_URL = f"{os.environ['RENDER_EXTERNAL_URL']}{settings.WEBHOOK_PATH}"
        logger.info(f"Constructed webhook URL: {settings.WEBHOOK_URL}")

    # -------------------------------------------------
    # 4a. WEBHOOK MODE  – aiohttp web-server
    # -------------------------------------------------
    if is_webhook_mode:
        # Tell Telegram to use the webhook
        await bot.set_webhook(settings.WEBHOOK_URL, drop_pending_updates=True)

        # Build aiohttp Application and register aiogram handler on given path
        app = web.Application()

        # Use Aiogram's built-in helper to register a proper request handler
        SimpleRequestHandler(dp, bot).register(app, path=settings.WEBHOOK_PATH)

        # Extra endpoints
        app.router.add_get("/", health_check)
        app.router.add_get("/health", health_check)
        app.router.add_static(
            "/reports/", path=str(settings.REPORT_DIR), name="reports"
        )

        # Launch web-server using the *current* event-loop.
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=settings.HOST, port=settings.PORT)
        await site.start()
        logger.info(f"Webhook server started on {settings.HOST}:{settings.PORT}")

        # Block forever (until Ctrl-C / container stop)
        await asyncio.Event().wait()

    # -------------------------------------------------
    # 4b. LONG-POLLING MODE
    # -------------------------------------------------
    else:
        logger.info("Starting long-polling")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    # -------------------------------------------------
    # 5. Graceful shutdown  (falls through when poll/webhook exits)
    # -------------------------------------------------
    scheduler.shutdown(wait=False)
    await bot.session.close()


if __name__ == "__main__":
    # On Windows use Selector loop for aiogram compatibility
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user – shutting down…")
    except Exception as e:
        logger.error(f"Unhandled exception in main(): {e}")
        if settings.SENTRY_DSN:
            sentry_sdk.capture_exception(e) 