import json
import logging
import time
from typing import List, Dict, Any, Tuple

import openai
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Meta-analysis prompt
META_PROMPT = """
Вы эксперт-психолог и терапевт отношений, специализирующийся на работах Габора Мате, Джона Готтмана, Маршалла Розенберга и Эрика Берна.

Я предоставлю вам данные в формате JSON, извлеченные из сообщений чата, которые содержат:
- автор
- временная_метка
- анализ_настроения (sentiment)
- оценка_токсичности (toxicity, 0-1)
- оценка_манипуляции (manipulation, 0-1)
- стиль_привязанности (attachment_style)
- паттерны_общения (communication_pattern)
- четыре_всадника_готтмана (gottman_horsemen)
- трансакционное_состояние (transactional_state)
- психологические_потребности
- ключевые_цитаты (key_quotes)

На основе этих данных создайте ПОДРОБНЫЙ и ГЛУБОКИЙ психологический отчет в формате HTML ПОЛНОСТЬЮ НА РУССКОМ ЯЗЫКЕ. Отчет должен быть исключительно детальным, с большим количеством цитат и проницательным анализом:

1. **Общий обзор** (минимум 600 слов): 
   - Подробная оценка динамики отношений с обширными примерами
   - Глубокий анализ с точки зрения теории привязанности Габора Мате
   - Оценка стабильности отношений во времени
   - Анализ баланса власти и взаимозависимости

2. **Паттерны общения** (минимум 500 слов):
   - Детальный анализ здоровых и проблемных паттернов с МИНИМУМ 5 конкретными примерами цитат
   - Подробный разбор присутствия каждого из Четырех Всадников Готтмана с конкретными цитатами и частотой их появления
   - Анализ соотношения позитивных к негативным взаимодействиям (Принцип Готтмана 5:1)
   - Оценка эмоциональной безопасности в коммуникации

3. **Анализ эмоций** (минимум 500 слов):
   - Подробное отслеживание эмоциональных колебаний с точными цитатами
   - Анализ эмоциональных триггеров каждого участника с конкретными примерами
   - Выявление ран привязанности по Габору Мате с глубоким анализом их происхождения
   - Детальный разбор эмоциональной регуляции и созависимости

4. **Токсичные взаимодействия** (минимум 300 слов):
   - Подробный анализ всех манипулятивных тактик с МИНИМУМ 4 конкретными примерами
   - Детальное описание нарушений границ с цитатами
   - Выявление потенциальных паттернов газлайтинга, обесценивания или других форм эмоционального насилия с примерами
   - Оценка уровня токсичности отношений в целом с конкретными доказательствами

5. **Ключевые цитаты** (минимум 15 цитат):
   - МИНИМУМ 15 наиболее значимых цитат из разговора, демонстрирующих ключевые аспекты отношений
   - Каждая цитата должна сопровождаться глубоким психологическим анализом (минимум 50 слов на каждую)
   - Распределение цитат должно быть равномерным между всеми участниками беседы
   - ВАЖНО: Если в данных есть поле с дополнительными цитатами, ОБЯЗАТЕЛЬНО включите их в этот раздел
   - Для каждой цитаты указывайте автора, эмоцию и стиль коммуникации
   - Оформляйте цитаты в отдельных блоках с классом "quote" для лучшей визуализации

6. **Психологические инсайты** (минимум 600 слов):
   - Глубокий анализ на основе Трансакционного анализа с подробным разбором эго-состояний и их взаимодействия
   - Детальный анализ стилей привязанности каждого участника с конкретными примерами их проявления
   - Выявление психологических защитных механизмов и их влияния на отношения
   - Анализ глубинных потребностей и мотивов поведения, не выраженных напрямую

7. **Рекомендации** (минимум 10 рекомендаций):
   - МИНИМУМ 10 конкретных, практических рекомендаций по улучшению отношений
   - Детальное объяснение каждой рекомендации (минимум 100 слов на каждую)
   - Конкретные упражнения и техники для применения в повседневной жизни
   - Специфические рекомендации для каждого участника отдельно

8. **Количественный анализ** (новый раздел):
   - Подробное описание всех количественных показателей, выявленных в анализе
   - Процентное соотношение различных паттернов коммуникации
   - Динамика изменения эмоционального фона с течением времени
   - Сравнительный анализ участников по психологическим метрикам

## ГРАФИЧЕСКАЯ ВИЗУАЛИЗАЦИЯ (улучшенная и расширенная):

1. **График временной шкалы настроений**:
   - Создайте ДЕТАЛЬНЫЙ интерактивный график, показывающий эмоциональные колебания каждого участника с течением времени
   - Используйте реальные количественные данные из анализа
   - Включите маркеры ключевых моментов с подписями
   - Используйте HTML/CSS для создания графика с градиентной цветовой схемой

2. **Лепестковая диаграмма коммуникационных метрик**:
   - Создайте для КАЖДОГО участника лепестковую диаграмму, отображающую следующие метрики:
     - Токсичность (средний показатель)
     - Манипулятивность (средний показатель)
     - Позитивность (процентное соотношение)
     - Ассертивность (процентное соотношение)
     - Эмпатия (рассчитанный показатель)
     - Эмоциональная регуляция (рассчитанный показатель)
   - Используйте точные количественные показатели из анализа данных

3. **Гистограммы распределения коммуникационных паттернов**:
   - Создайте детальную гистограмму для каждого участника, показывающую распределение стилей коммуникации
   - Включите процентные соотношения и абсолютные значения
   - Добавьте сравнительный график между участниками

4. **Тепловая карта эмоциональной динамики**:
   - Создайте тепловую карту на основе сентимент-анализа всего разговора
   - Визуализируйте эмоциональную интенсивность в разные периоды беседы
   - Используйте градиентную цветовую шкалу для отображения интенсивности эмоций

5. **График присутствия "Четырех Всадников" Готтмана**:
   - Визуализируйте частоту появления каждого из "Четырех Всадников" на протяжении разговора
   - Создайте сравнительную диаграмму между участниками
   - Включите индикатор общего риска для отношений на основе методики Готтмана

6. **Диаграмма Санкей трансакционных взаимодействий**:
   - Создайте диаграмму Санкей, отображающую потоки взаимодействий между эго-состояниями
   - Визуализируйте, как часто встречаются различные комбинации взаимодействий (Родитель-Ребенок, Взрослый-Взрослый и т.д.)
   - Используйте ширину потоков для отображения частоты взаимодействий

7. **График динамики психологических потребностей**:
   - Визуализируйте, как меняются выраженные психологические потребности с течением диалога
   - Отметьте удовлетворенные и неудовлетворенные потребности разными цветами
   - Включите метрики выражения потребностей для каждого участника

## РЕКОМЕНДАЦИИ ПО СТИЛЮ:

1. Используйте профессиональный, чистый дизайн с успокаивающей цветовой схемой.
2. Включите ВСЕ перечисленные выше графики и визуальные элементы, используя встроенный в HTML JavaScript и CSS.
3. Используйте адекватные размеры шрифта, отступы и поля для удобочитаемости.
4. HTML должен быть полностью автономным со встроенным CSS и JavaScript (без внешних зависимостей).
5. ОБЯЗАТЕЛЬНО реализуйте графики и диаграммы, используя встроенный SVG и CSS.
6. Сделайте отчет похожим на профессиональный психологический анализ высшего уровня.
7. Включите заголовок с названием "Chat X-Ray: Подробный психологический анализ отношений" и текущей датой.
8. Для раздела "Ключевые цитаты" используйте следующий HTML шаблон для каждой цитаты:
   ```html
   <div class="quote">
     <p>"Текст цитаты здесь"</p>
     <p class="quote-author">Автор цитаты</p>
     <p class="quote-emotion">Эмоция: [эмоция] | Стиль общения: [стиль]</p>
     <p>Психологический анализ: [ваш анализ цитаты]</p>
   </div>
   ```

## КЛЮЧЕВЫЕ ТРЕБОВАНИЯ:
1. ОБЯЗАТЕЛЬНО ПИШИТЕ ВЕСЬ ТЕКСТ ОТЧЕТА НА РУССКОМ ЯЗЫКЕ БЕЗ ИСКЛЮЧЕНИЙ.
2. Используйте ТОЧНЫЕ количественные показатели из данных для создания всех графиков и диаграмм.
3. Включите МИНИМУМ 30 содержательных цитат с подробным анализом.
4. Общий объём отчёта — не менее 3 500 слов (≈ 4 страниц A4).
5. Сделайте отчёт МАКСИМАЛЬНО ГЛУБОКИМ и ПРОНИЦАТЕЛЬНЫМ, как если бы его подготовил ведущий эксперт в психологии отношений.
6. ВСЕ ГРАФИКИ ДОЛЖНЫ БЫТЬ СОЗДАНЫ на основе РЕАЛЬНЫХ ДАННЫХ анализа и находиться прямо в HTML (SVG/CSS/JS).
7. ОБЯЗАТЕЛЬНО включите ВСЕ цитаты, которые были предоставлены в дополнительных данных, даже если они отсутствуют в основной выборке.
8. Убедитесь, что итоговый HTML легко конвертируется в PDF без потери форматирования.

Ваш вывод должен быть ТОЛЬКО допустимым HTML (со встроенным CSS и JavaScript), который можно напрямую преобразовать в PDF.
"""


async def generate_meta_report(results: List[Dict[str, Any]], max_retries: int = 3) -> Tuple[str, int]:
    """
    Generate a meta report from the analysis results using GPT-4 Turbo.
    
    Args:
        results: List of analyzed message dictionaries
        max_retries: Maximum number of retries on rate limit errors
        
    Returns:
        Tuple containing HTML string for the report and tokens used for the report
    """
    # Calculate approximate token count for the dataset
    def estimate_tokens(data_str: str) -> int:
        # Each character is approximately 0.25 tokens for UTF-8 text
        return int(len(data_str) * 0.25)
    
    # Function to get a balanced sample from messages
    def get_balanced_sample(msgs, target_size):
        if len(msgs) <= target_size:
            return msgs
            
        # Calculate how many messages to take from each section
        section_size = target_size // 3
        
        # Ensure we have at least some messages from each section
        first_section = msgs[:section_size]
        
        # For middle section, pick from the actual middle
        middle_start = max(section_size, len(msgs) // 2 - section_size // 2)
        middle_end = min(middle_start + section_size, len(msgs))
        middle_section = msgs[middle_start:middle_end]
        
        # Last section
        last_section = msgs[-section_size:]
        
        return first_section + middle_section + last_section
    
    # Extract key quotes from all messages for preservation
    def extract_key_quotes(msgs):
        quotes = []
        for msg in msgs:
            if "key_quotes" in msg and msg["key_quotes"]:
                for quote in msg["key_quotes"]:
                    if quote and len(quote) > 5:  # Ensure it's a meaningful quote
                        quotes.append({
                            "quote": quote,
                            "author": msg.get("author", "Unknown"),
                            "sentiment": msg.get("sentiment", "neutral"),
                            "emotion": msg.get("emotion", "unknown")
                        })
        return quotes
    
    # We're using GPT-4 Turbo which has a 128K token context window,
    # but we need to be more careful with sampling for large chats
    
    # Extract all key quotes from the original results for preservation
    all_key_quotes = extract_key_quotes(results)
    logger.info(f"Extracted {len(all_key_quotes)} key quotes for preservation")
    
    # Start with an optimistic sampling approach
    max_context_tokens = 110000  # Leave room for prompt and response
    target_token_budget = 90000

    def strip_bulky_fields(msg_list):
        """Return a deep-copied list with heavy fields removed."""
        cleaned = []
        for m in msg_list:
            m_copy = m.copy()
            # Remove or truncate very large fields that are not essential
            m_copy.pop("key_quotes", None)  # quotes will be handled separately
            cleaned.append(m_copy)
        return cleaned

    # Work with a cleaned copy for token estimation / sending
    results_to_process_clean = strip_bulky_fields(results)
    results_json = json.dumps(results_to_process_clean, indent=None)
    estimated_tokens = estimate_tokens(results_json)

    # Iteratively shrink until we are under the budget
    minimal_sample_size = 90
    current_target_size = len(results_to_process_clean)
    while estimated_tokens > target_token_budget and current_target_size > minimal_sample_size:
        current_target_size = max(minimal_sample_size, int(current_target_size * 0.8))
        results_to_process_clean = strip_bulky_fields(get_balanced_sample(results, current_target_size))
        results_json = json.dumps(results_to_process_clean, indent=None)
        estimated_tokens = estimate_tokens(results_json)
        logger.info(f"Adaptive reduction: {current_target_size} msgs, est {estimated_tokens} tokens")

    # Ensure we operate with the cleaned, size-constrained data going forward
    results_to_process = results_to_process_clean

    retry_count = 0
    backoff_time = settings.RETRY_DELAY_SECONDS  # Start with configured delay
    
    while retry_count <= max_retries:
        try:
            # Preserve quotes if we had to reduce the dataset
            quotes_prompt = ""
            if len(results_to_process) < len(results) and all_key_quotes:
                quotes_json = json.dumps(all_key_quotes[:50], indent=None, ensure_ascii=False)  # Limit to 50 most important quotes
                quotes_prompt = f"""
                ВАЖНО: Включите эти ключевые цитаты в раздел "Ключевые цитаты", даже если они не присутствуют в сокращенной выборке сообщений:
                {quotes_json}
                """
            
            async def _gpt_call(section_hint: str, include_doctype: bool) -> Tuple[str, int]:
                """Helper to call GPT with a hint which sections to produce."""
                sys_prompt = META_PROMPT + f"\nОГРАНИЧЕНИЕ: Сгенерируй ТОЛЬКО {section_hint}."
                if not include_doctype:
                    sys_prompt += " Не добавляй <!DOCTYPE html> и теги <html> <head>. Начни сразу с содержимого <body>."

                resp = await client.chat.completions.create(
                    model=settings.META_MODEL,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": f"На основе данных:\n\n{results_json}\n\n{quotes_prompt}"}
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                    n=1
                )
                content = resp.choices[0].message.content
                t_used = resp.usage.total_tokens if hasattr(resp, "usage") and resp.usage else 0
                return content, t_used

            # --- First half (sections 1-4) ---
            html_part1, tokens1 = await _gpt_call("разделы 1-4 (Обзор, Паттерны, Эмоции, Токсичные взаимодействия)", True)

            # --- Second half (sections 5-8 + графика) ---
            # Strengthen requirements for graphics in the second part
            second_hint = (
                "разделы 5-8 (Цитаты, Инсайты, Рекомендации, Количественный анализ) И ОБЯЗАТЕЛЬНО минимум 5 SVG графиков. "
                "Каждый график должен иметь уникальный id вида 'chart-1', 'chart-2', ... и подпись. Не используй внешние библиотеки." 
            )
            html_part2_raw, tokens2 = await _gpt_call(second_hint, False)

            # --- Inject additional CSS for better readability ---
            def _inject_css(html: str) -> str:
                import re
                style_block = """
                <style>
                    body { font-size: 17px; line-height: 1.8; }
                    h2 { font-size: 24px; margin-top: 40px; }
                    svg text { font-family: Arial, sans-serif; font-size: 14px; }
                </style>
                """
                head_match = re.search(r"<head[^>]*>", html, re.IGNORECASE)
                if head_match:
                    insert_pos = head_match.end()
                    html = html[:insert_pos] + style_block + html[insert_pos:]
                return html

            # Merge: insert part2 before </body>
            import re
            body_close_re = re.compile(r"</body>\s*</html>\s*$", re.IGNORECASE | re.DOTALL)
            match = body_close_re.search(html_part1)
            if match:
                html_content = body_close_re.sub(html_part2_raw + match.group(0), html_part1)
            else:
                # Fallback – just concatenate
                html_content = html_part1 + html_part2_raw

            # Inject additional CSS for better readability
            html_content = _inject_css(html_content)

            tokens_used_meta = tokens1 + tokens2
            
            # Strip any leading non-HTML text the model might have added (e.g. "Конечно, вот отчёт:")
            import re
            leading_html_match = re.search(r'(<!DOCTYPE html[\s\S]*|<html[\s\S]*)', html_content, re.IGNORECASE)
            if leading_html_match:
                html_content = leading_html_match.group(1).lstrip()

            # Basic validation - check if it looks like HTML (case-insensitive)
            _html_start = html_content.lstrip()[:40].lower()
            if not (_html_start.startswith("<!doctype html") or _html_start.startswith("<html")):
                # Try to extract an HTML block if the model included additional text before/after
                html_match = re.search(r'(<html[\s\S]*?</html>)', html_content, re.IGNORECASE)
                if html_match:
                    html_content = html_match.group(1)
                else:
                    # Wrap the content in basic HTML if needed
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Chat X-Ray: Психологический анализ отношений</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
                            h2 {{ color: #3498db; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                            .section {{ margin-bottom: 30px; }}
                            .quote {{ font-style: italic; border-left: 3px solid #3498db; padding: 15px; margin: 15px 0; background-color: #f8f9fa; }}
                            .quote-author {{ font-weight: bold; margin-top: 5px; color: #555; }}
                            .quote-emotion {{ color: #777; font-size: 0.9em; margin-top: 5px; }}
                            .recommendation {{ background-color: #f0f7fb; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #3498db; }}
                            .chart {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 20px 0; height: 300px; display: flex; justify-content: center; align-items: center; }}
                            .chart-placeholder {{ color: #777; font-style: italic; }}
                            .positive {{ color: #27ae60; }}
                            .negative {{ color: #e74c3c; }}
                            .neutral {{ color: #7f8c8d; }}
                            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <h1>Chat X-Ray: Психологический анализ отношений</h1>
                        
                        <div class="section">
                            <h2>Общий обзор</h2>
                            <p>Данный отчет содержит психологический анализ предоставленного чата, основываясь на теориях Габора Мате, Джона Готтмана и других психологов.</p>
                            {html_content}
                        </div>
                        
                        <div class="section">
                            <h2>Паттерны общения</h2>
                            <p>В данном разделе представлен анализ основных паттернов общения между участниками беседы.</p>
                            <div class="chart">
                                <p class="chart-placeholder">Здесь будет отображаться график коммуникационных паттернов.</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Анализ эмоций</h2>
                            <p>Анализ эмоционального фона беседы и динамики эмоций участников.</p>
                            <div class="chart">
                                <p class="chart-placeholder">Здесь будет отображаться график эмоционального состояния.</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Ключевые цитаты</h2>
                            <p>Наиболее значимые цитаты из беседы с психологическим анализом:</p>
                            <div class="quote">
                                <p>"Пример цитаты из беседы, которая демонстрирует важный психологический аспект отношений."</p>
                                <p class="quote-author">Автор цитаты</p>
                                <p class="quote-emotion">Эмоция: радость | Стиль общения: ассертивный</p>
                                <p>Психологический анализ: Данная цитата демонстрирует открытость в общении и стремление к установлению эмоциональной связи.</p>
                            </div>
                            <div class="quote">
                                <p>"Еще один пример значимой цитаты из беседы."</p>
                                <p class="quote-author">Другой участник</p>
                                <p class="quote-emotion">Эмоция: грусть | Стиль общения: пассивный</p>
                                <p>Психологический анализ: В этой цитате проявляется неуверенность и страх отвержения, характерные для тревожного стиля привязанности.</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Психологические инсайты</h2>
                            <p>Психологические наблюдения на основе трансакционного анализа и теории привязанности.</p>
                        </div>
                        
                        <div class="section">
                            <h2>Рекомендации</h2>
                            <div class="recommendation">
                                <p>Рекомендация 1: Улучшить коммуникацию и практиковать активное слушание, чтобы лучше понимать потребности друг друга.</p>
                            </div>
                            <div class="recommendation">
                                <p>Рекомендация 2: Обратить внимание на эмоциональные триггеры и практиковать осознанность в моменты напряжения.</p>
                            </div>
                            <div class="recommendation">
                                <p>Рекомендация 3: Использовать технику "Я-сообщений" вместо обвинений для выражения своих чувств и потребностей.</p>
                            </div>
                            <div class="recommendation">
                                <p>Рекомендация 4: Выделять специальное время для обсуждения важных вопросов, избегая спонтанных серьезных разговоров в неподходящее время.</p>
                            </div>
                            <div class="recommendation">
                                <p>Рекомендация 5: Регулярно выражать признательность и благодарность друг другу, укрепляя позитивную связь.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
            
            # Add 'viewport' meta tag if it's not already present
            if "<meta name=\"viewport\"" not in html_content:
                html_content = html_content.replace("<head>", 
                    "<head>\n        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
                
            # Add sampling disclaimer if applicable
            if len(results_to_process) < len(results):
                # Add a note about sampling at the top of the report
                import re
                
                # Try to find where to insert our sampling notice
                body_pattern = r'<body[^>]*>'
                if re.search(body_pattern, html_content):
                    # Insert after the body tag
                    sampling_notice = f"""
                    <div style="background-color: #fff3cd; padding: 15px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #ffeeba;">
                        <strong>Примечание:</strong> Этот анализ основан на выборке из {len(results_to_process)} сообщений из общего объема вашей беседы ({len(results)} сообщений).
                        Выборка включает начало, середину и конец вашего чата для обеспечения сбалансированного анализа.
                    </div>
                    """
                    html_content = re.sub(body_pattern, lambda m: m.group(0) + sampling_notice, html_content)
            
            # --- Insert banner with total messages analysed ---
            msg_banner = (
                f"""
                <div style=\"background-color:#e8f4fd;padding:12px;margin-bottom:20px;border-left:4px solid #3498db;\">
                    Отчёт подготовлен после анализа <b>{len(results)}</b> сообщений обеих сторон.
                </div>
                """
            )
            body_tag_re = re.compile(r"<body[^>]*>", re.IGNORECASE)
            html_content, subs = body_tag_re.subn(lambda m: m.group(0)+msg_banner, html_content, count=1)
            if subs == 0:
                html_content = msg_banner + html_content
            
            return html_content, tokens_used_meta
            
        except openai.RateLimitError as e:
            retry_count += 1
            logger.warning(f"Rate limit exceeded (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count <= max_retries:
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
                
                # If this is the last retry, reduce the sample size further
                if retry_count == max_retries and len(results_to_process) > 150:
                    # Reduce to about 150 messages for the final attempt
                    results_to_process = get_balanced_sample(results, 150)
                    results_json = json.dumps(results_to_process, indent=None)
                    logger.info(f"Финальная попытка с уменьшенной выборкой из {len(results_to_process)} сообщений")
            else:
                logger.error("Достигнуто максимальное количество попыток. Возвращаем шаблон ошибки.")
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Chat X-Ray: Ошибка отчета</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        h1 {{ color: #e74c3c; text-align: center; }}
                        .error {{ background-color: #f8d7da; padding: 20px; border-radius: 5px; }}
                        .suggestion {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <h1>Ошибка при создании отчета</h1>
                    <div class="error">
                        <p>При анализе вашего чата произошла ошибка:</p>
                        <p><strong>{str(e)}</strong></p>
                        <p>Пожалуйста, попробуйте еще раз позже или обратитесь в службу поддержки, если проблема не исчезнет.</p>
                    </div>
                    <div class="suggestion">
                        <p><strong>Возможные решения:</strong></p>
                        <ul>
                            <li>Загрузите файл меньшего размера</li>
                            <li>Убедитесь, что файл содержит текстовые сообщения в правильном формате</li>
                            <li>Попробуйте снова через несколько минут</li>
                        </ul>
                    </div>
                </body>
                </html>
                """, 0
                
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error in meta analysis: {e}")
            
            if "context_length_exceeded" in str(e):
                # Handle context length exceeded error specifically
                logger.warning("Context length exceeded, trying with a minimal sample")
                
                # Use a much smaller sample for this retry
                minimal_sample_size = 90
                minimal_sample = get_balanced_sample(results, minimal_sample_size)
                results_json = json.dumps(minimal_sample, indent=None)
                
                logger.info(f"Retrying with minimal sample of {len(minimal_sample)} messages")
                
                # Generate quotes prompt from all key quotes
                quotes_prompt = ""
                if all_key_quotes:
                    quotes_json = json.dumps(all_key_quotes[:30], indent=None, ensure_ascii=False)  # Limit to 30 most important quotes
                    quotes_prompt = f"""
                    ВАЖНО: Включите эти ключевые цитаты в раздел "Ключевые цитаты", даже если они не присутствуют в сокращенной выборке сообщений:
                    {quotes_json}
                    """
                
                # Try once more with the minimal sample
                try:
                    response = await client.chat.completions.create(
                        model=settings.META_MODEL,
                        messages=[
                            {"role": "system", "content": META_PROMPT},
                            {"role": "user", "content": f"Создайте психологический отчет на РУССКОМ языке на основе этой выборки сообщений:\n\n{results_json}\n\n{quotes_prompt}"}
                        ],
                        temperature=0.7,
                        max_tokens=4096,
                        n=1
                    )
                    
                    html_content = response.choices[0].message.content
                    tokens_used_meta = response.usage.total_tokens if hasattr(response, "usage") and response.usage else 0
                    
                    # Add sampling disclaimer
                    import re
                    body_pattern = r'<body[^>]*>'
                    if re.search(body_pattern, html_content):
                        sampling_notice = f"""
                        <div style="background-color: #fff3cd; padding: 15px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #ffeeba;">
                            <strong>Примечание:</strong> Из-за большого размера вашей беседы ({len(results)} сообщений), 
                            анализ основан на минимальной выборке из {len(minimal_sample)} сообщений, чтобы обеспечить 
                            оптимальную работу искусственного интеллекта. Выборка включает сообщения из начала, 
                            середины и конца вашего чата для обеспечения сбалансированного анализа.
                        </div>
                        """
                        html_content = re.sub(body_pattern, lambda m: m.group(0) + sampling_notice, html_content)
                        
                    return html_content, tokens_used_meta
                except Exception as inner_error:
                    logger.error(f"Error in retry with minimal sample: {inner_error}")
            
            # Return a basic error HTML
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Chat X-Ray: Ошибка отчета</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    h1 {{ color: #e74c3c; text-align: center; }}
                    .error {{ background-color: #f8d7da; padding: 20px; border-radius: 5px; }}
                    .suggestion {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h1>Ошибка при создании отчета</h1>
                <div class="error">
                    <p>При анализе вашего чата произошла ошибка:</p>
                    <p><strong>{str(e)}</strong></p>
                    <p>Пожалуйста, попробуйте еще раз позже или обратитесь в службу поддержки, если проблема не исчезнет.</p>
                </div>
                <div class="suggestion">
                    <p><strong>Возможные решения:</strong></p>
                    <ul>
                        <li>Загрузите файл меньшего размера</li>
                        <li>Убедитесь, что файл содержит текстовые сообщения в правильном формате</li>
                        <li>Попробуйте снова через несколько минут</li>
                    </ul>
                </div>
            </body>
            </html>
            """, 0 