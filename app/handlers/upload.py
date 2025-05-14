import logging
import os
import uuid
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from app.config import settings
from app.services.chunker import split_chat
from app.services.llm_primary import process_chunks
from app.services.llm_meta import generate_meta_report
from app.services.render import render_to_pdf
from app.utils.logging_utils import log_cost

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.document)
async def handle_document(message: Message):
    """Handle document uploads and process valid text files"""
    # Check if document exists
    if not message.document:
        await message.answer("⚠️ Документ не найден. Пожалуйста, отправьте текстовый файл.")
        return
    
    # Check MIME type
    if message.document.mime_type != "text/plain":
        await message.answer(
            "⚠️ Неверный формат файла. Пожалуйста, отправьте только текстовый файл (.txt)."
        )
        return
    
    # Check file size
    if message.document.file_size > settings.MAX_FILE_SIZE:
        await message.answer(
            f"⚠️ Файл слишком большой. Максимальный размер {settings.MAX_FILE_SIZE // (1024 * 1024)} МБ."
        )
        return
    
    # All checks passed, let's download and process the file
    await message.answer("✅ Ваш файл получен. Начинаю анализ...")
    
    # Generate unique IDs for the files
    file_id = str(uuid.uuid4())
    upload_file_path = settings.UPLOAD_DIR / f"{file_id}.txt"
    report_file_path = settings.REPORT_DIR / f"{file_id}.pdf"
    html_file_path = settings.REPORT_DIR / f"{file_id}.html"
    
    try:
        # Download the file
        await message.bot.download(
            message.document,
            destination=upload_file_path
        )
        
        # Let the user know we're processing
        status_message = await message.answer("🔍 Анализирую чат... Это может занять минуту или две.")
        
        # Split the chat into chunks
        chunks = split_chat(upload_file_path)
        num_chunks = len(chunks)
        
        if num_chunks == 0:
            await message.answer("⚠️ Не удалось обработать файл. Возможно, он пуст или имеет неправильный формат?")
            os.unlink(upload_file_path)
            return
        
        # Process chunks with GPT-3.5
        await status_message.edit_text(f"🔄 Обрабатываю {num_chunks} фрагментов данных чата...")
        analysis_results = await process_chunks(chunks)
        
        # Generate meta report with GPT-4
        await status_message.edit_text("✨ Создаю психологические выводы и генерирую отчет...")
        html_content = await generate_meta_report(analysis_results)
        
        # Save HTML content to file
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Render HTML to PDF
        pdf_url = await render_to_pdf(html_file_path, report_file_path)
        
        # Generate a public URL for the PDF
        report_url = f"{settings.WEBHOOK_HOST}/reports/{os.path.basename(report_file_path)}" if settings.WEBHOOK_HOST else f"file://{report_file_path}"
        
        # Calculate and log approximate cost
        approx_cost = (num_chunks * 0.0005) + 0.03  # Approximate cost: $0.0005 per chunk for GPT-3.5 + $0.03 for GPT-4
        await log_cost(message.from_user.id, num_chunks, approx_cost)
        
        # Send success message with download option
        await status_message.delete()
        
        # If we're in local mode without a webhook, just send the file directly
        if not settings.WEBHOOK_HOST:
            await message.answer(
                "🎉 Анализ завершен! Вот ваш психологический отчет об отношениях:",
                reply_markup=None
            )
            await message.answer_document(
                FSInputFile(report_file_path),
                caption="Ваш отчет Chat X-Ray готов. Этот файл будет доступен в течение 72 часов."
            )
        else:
            # In production with webhook, send a link
            await message.answer(
                f"🎉 Ваш отчет Chat X-Ray готов!\n\n"
                f"<b>Скачать отчет:</b> <a href='{report_url}'>Психологический анализ отношений</a>\n\n"
                f"Этот отчет будет доступен в течение 72 часов."
            )
        
        # Add metadata to track file expiration
        expiration_time = datetime.now().timestamp() + (settings.REPORT_RETENTION_HOURS * 3600)
        with open(f"{report_file_path}.meta", "w") as f:
            f.write(str(expiration_time))
        
        # Delete the original upload file metadata
        upload_expiration_time = datetime.now().timestamp() + (settings.UPLOAD_RETENTION_HOURS * 3600)
        with open(f"{upload_file_path}.meta", "w") as f:
            f.write(str(upload_expiration_time))
            
    except Exception as e:
        logger.exception(f"Error processing file: {e}")
        if settings.SENTRY_DSN:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        
        await message.answer(
            "❌ Извините, произошла ошибка при обработке вашего файла. Пожалуйста, попробуйте позже."
        )
        
        # Make sure to clean up any files if there was an error
        if os.path.exists(upload_file_path):
            os.unlink(upload_file_path)
        if os.path.exists(html_file_path):
            os.unlink(html_file_path)
        if os.path.exists(report_file_path):
            os.unlink(report_file_path) 