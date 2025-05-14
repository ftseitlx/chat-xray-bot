import asyncio
import os
import sys
from pathlib import Path

import openai

from app.services.chunker import split_chat
from app.services.llm_primary import process_chunks
from app.services.llm_meta import generate_meta_report
from app.services.render import render_to_pdf
from app.utils.logging_utils import log_cost
from app.config import settings


async def main():
    # Use the Russian sample chat file
    sample_file_path = Path("test_chat_russian.txt")
    
    if not sample_file_path.exists():
        print(f"Ошибка: Файл {sample_file_path} не найден")
        return
    
    # Make sure output directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    
    print(f"Обработка тестового чата: {sample_file_path}")
    
    # Generate unique IDs for the files
    file_id = "test_russian"
    report_file_path = settings.REPORT_DIR / f"{file_id}.pdf"
    html_file_path = settings.REPORT_DIR / f"{file_id}.html"
    
    try:
        print("Шаг 1: Разделение чата на фрагменты...")
        chunks = split_chat(sample_file_path)
        num_chunks = len(chunks)
        print(f"  - Разделено на {num_chunks} фрагментов")
        
        print("\nШаг 2: Обработка фрагментов с помощью GPT-3.5 Turbo...")
        try:
            analysis_results = await process_chunks(chunks)
            print(f"  - Обработано {len(analysis_results)} сообщений")
            
            # Save intermediate results for debugging
            import json
            with open(settings.REPORT_DIR / f"{file_id}_analysis.json", "w", encoding="utf-8") as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            print(f"  - Промежуточные результаты сохранены в {settings.REPORT_DIR / f'{file_id}_analysis.json'}")
            
        except openai.RateLimitError as e:
            print(f"  ❌ Превышен лимит запросов API: {e}")
            print("  - Попробуйте обработать меньше сообщений или повторите попытку позже")
            return
        
        print("\nШаг 3: Создание мета-отчета с помощью GPT-4...")
        try:
            html_content = await generate_meta_report(analysis_results)
            print("  - Сгенерирован HTML-отчет")
            
            # Save HTML content to file
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"  - HTML сохранен в {html_file_path}")
        except openai.RateLimitError as e:
            print(f"  ❌ Превышен лимит запросов API при создании мета-анализа: {e}")
            print("  - Сохранение промежуточных результатов...")
            return
        
        print("\nШаг 4: Рендеринг HTML в PDF...")
        try:
            pdf_url = await render_to_pdf(html_file_path, report_file_path)
            print(f"  - PDF доступен по адресу: {pdf_url}")
        except Exception as e:
            print(f"  ⚠️ Ошибка рендеринга PDF: {e}")
            print("  - HTML-отчет все равно доступен")
        
        # Log approximate cost
        approx_cost = (num_chunks * 0.0005) + 0.01  # $0.0005 per chunk for GPT-3.5 + $0.01 for GPT-4 Turbo
        await log_cost("test_user", num_chunks, approx_cost)
        print(f"\nПриблизительная стоимость: ${approx_cost:.4f}")
        
        print("\nПроцесс успешно завершен!")
        print(f"Просмотрите PDF-отчет: {report_file_path}")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время обработки: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПроцесс прерван пользователем")
        sys.exit(0) 