import json
import logging
import time
import asyncio
from typing import List, Dict, Any, Tuple

import openai
from openai import AsyncOpenAI

from app.config import settings
from app.services.graphics import (
    generate_sentiment_timeline_svg,
    generate_radar_chart_svg,
    generate_bar_chart_svg,
)

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

На основе этих данных создайте ПОДРОБНЫЙ и ГЛУБОКИЙ психологический отчет в формате HTML ПОЛНОСТЬЮ НА РУССКОМ ЯЗЫКЕ. Отчет должен быть исключительно детальным, с большим количеством цитат и проницательным анализом. Он будет состоять из следующих разделов:

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

5. **Ключевые цитаты** (минимум 60 цитат):
   - МИНИМУМ 60 наиболее значимых цитат из разговора, демонстрирующих ключевые аспекты отношений
   - Каждая цитата должна сопровождаться глубоким психологическим анализом (минимум 50 слов на каждую)
   - Распределение цитат должно быть равномерным между всеми участниками беседы
   - ВАЖНО: Если в данных есть поле с дополнительными цитатами (передаются в `quotes_prompt`), ОБЯЗАТЕЛЬНО включите их в этот раздел
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

8. **Количественный анализ и Визуализация Данных**:
   - В этом разделе предоставьте текстовый анализ и ключевые выводы для следующих типов визуализаций. Графики будут созданы программно и вставлены в HTML на место соответствующих заполнителей (`<p class="chart-placeholder">...</p>`). Используйте данные из `AGG_METRICS` и `results_json` для вашего анализа.
   - **8.1. Анализ временной шкалы настроений**: Опишите эмоциональные колебания каждого участника с течением времени, ссылаясь на данные, которые будут визуализированы.
   - **8.2. Анализ коммуникационных метрик (Лепестковая диаграмма)**: Для каждого участника проанализируйте ключевые коммуникационные метрики (токсичность, манипулятивность, позитивность, ассертивность, эмпатия, эмоциональная регуляция), которые будут отображены на лепестковой диаграмме.
   - **8.3. Анализ распределения коммуникационных паттернов (Гистограммы)**: Опишите распределение стилей коммуникации для каждого участника.
   - **8.4. Анализ тепловой карты эмоциональной динамики**: Проанализируйте общую эмоциональную интенсивность и ее изменения в разные периоды беседы.
   - **8.5. Анализ "Четырех Всадников" Готтмана (График присутствия)**: Обсудите частоту появления каждого из "Всадников" и общий риск для отношений.
   - **8.6. Анализ трансакционных взаимодействий (Диаграмма Санкей)**: Опишите потоки взаимодействий между эго-состояниями (Родитель-Ребенок, Взрослый-Взрослый и т.д.).
   - **8.7. Анализ динамики психологических потребностей**: Обсудите, как меняются выраженные психологические потребности с течением диалога.

9. **Индивидуальный психологический портрет каждого участника** (минимум 500 слов на участника):
   - Для КАЖДОГО собеседника создайте отдельный под-раздел
   - Суммируйте его основные эмоции, потребности, паттерны общения
   - Привяжите анализ к КОНКРЕТНЫМ цитатам (укажите номера/текст цитат из раздела 5)
   - Опишите сильные стороны, уязвимости и ключевые триггеры

## РЕКОМЕНДАЦИИ ПО СТИЛЮ HTML:
1. Используйте профессиональный, чистый дизайн с успокаивающей цветовой схемой.
2. Используйте адекватные размеры шрифта, отступы и поля для удобочитаемости.
3. HTML должен быть полностью автономным со встроенным CSS (без внешних зависимостей JavaScript, если это не для графиков).
4. Сделайте отчет похожим на профессиональный психологический анализ высшего уровня.
5. Включите заголовок с названием "Chat X-Ray: Подробный психологический анализ отношений" и текущей датой.
6. Для раздела "Ключевые цитаты" используйте следующий HTML шаблон для каждой цитаты:
   \`\`\`html
   <div class="quote">
     <p>"Текст цитаты здесь"</p>
     <p class="quote-author">Автор цитаты</p>
     <p class="quote-emotion">Эмоция: [эмоция] | Стиль общения: [стиль]</p>
     <p>Психологический анализ: [ваш анализ цитаты]</p>
   </div>
   \`\`\`
   Местозаполнители для графиков будут иметь вид `<p class="chart-placeholder">Здесь будет график...</p>`. Ваша задача - предоставить текстовый контент ВОКРУГ этих местозаполнителей.

## КЛЮЧЕВЫЕ ТРЕБОВАНИЯ:
1. ОБЯЗАТЕЛЬНО ПИШИТЕ ВЕСЬ ТЕКСТ ОТЧЕТА НА РУССКОМ ЯЗЫКЕ БЕЗ ИСКЛЮЧЕНИЙ.
2. Используйте ТОЧНЫЕ количественные показатели из предоставленных данных (`results_json`, `AGG_METRICS`) для вашего анализа и особенно для раздела "Количественный анализ и Визуализация Данных".
3. Включите МИНИМУМ 60 содержательных цитат с подробным анализом в Разделе 5.
4. Общий объём отчёта — не менее 3 500 слов.
5. Сделайте отчёт МАКСИМАЛЬНО ГЛУБОКИМ и ПРОНИЦАТЕЛЬНЫМ.
6. ОБЯЗАТЕЛЬНО включите ВСЕ цитаты, которые были предоставлены в дополнительных данных (`quotes_prompt`), даже если они отсутствуют в основной выборке `results_json`.
7. СТРОГО ЗАПРЕЩЕНО придумывать или искажать цитаты — используйте ТОЛЬКО фактические цитаты.
8. Убедитесь, что итоговый HTML легко конвертируется в PDF без потери форматирования.
9. Включите отдельный под-раздел для КАЖДОГО участника с подробным психологическим портретом.

Ваш вывод должен быть ТОЛЬКО допустимым HTML (со встроенным CSS), который можно напрямую преобразовать в PDF. Начните с `<!DOCTYPE html>`.
"""


async def generate_meta_report(results: List[Dict[str, Any]], total_messages:int, max_retries: int = 3) -> Tuple[str, int]:
    """
    Generate a meta report from the analysis results using a single call to settings.META_MODEL.
    """
    def estimate_tokens(data_str: str) -> int:
        return int(len(data_str) * 0.25) # Rough estimate

    def get_balanced_sample(msgs, target_size):
        if not msgs or target_size <= 0:
            return []
        if len(msgs) <= target_size:
            return msgs
        section_size = max(1, target_size // 3)
        first_section = msgs[:section_size]
        middle_start = max(section_size, len(msgs) // 2 - section_size // 2)
        middle_end = min(middle_start + section_size, len(msgs) - section_size) # Ensure space for last_section
        middle_section = msgs[middle_start:middle_end]
        # Adjust last_section size if middle_section was smaller than expected
        remaining_for_last = target_size - (len(first_section) + len(middle_section))
        actual_last_section_size = max(0, min(section_size, remaining_for_last, len(msgs) - (middle_end if middle_section else section_size)))

        last_section = msgs[-actual_last_section_size:] if actual_last_section_size > 0 else []
        
        # Ensure sections don't overlap for very small target_size relative to msgs length
        # This simple concatenation might lead to fewer than target_size if actual_last_section_size becomes 0
        # or if sections overlap due to rounding. A more robust sampling might be needed for edge cases.
        # However, for typical use (target_size much smaller than len(msgs)), this should be fine.
        sampled_msgs = first_section + middle_section + last_section
        # If still over target, truncate
        return sampled_msgs[:target_size]


    def extract_key_quotes(msgs):
        quotes = []
        for msg in msgs:
            if "key_quotes" in msg and msg["key_quotes"]:
                for quote_text in msg["key_quotes"]: # Assuming key_quotes is a list of strings
                    if quote_text and len(quote_text) > 5:
                        quotes.append({
                            "quote": quote_text,
                            "author": msg.get("author", "Unknown"),
                            "sentiment": msg.get("sentiment_score", 0), # Use score for consistency
                            "emotion": msg.get("emotion", "unknown")
                        })
        return quotes

    all_key_quotes = extract_key_quotes(results)
    logger.info(f"Extracted {len(all_key_quotes)} key quotes for preservation.")

    from collections import defaultdict
    def compute_metrics_summary(msgs):
        per_author = defaultdict(lambda: defaultdict(list))
        for m in msgs:
            author = m.get("author", "Unknown")
            for field in ["sentiment_score", "toxicity", "manipulation", "empathy", "assertiveness", "emotion_intensity"]:
                val = m.get(field)
                if isinstance(val, (int, float)): per_author[author][field].append(val)
            horsemen = m.get("gottman_horsemen", {})
            for hk, hv in (horsemen or {}).items():
                if isinstance(hv, (int, float)): per_author[author][f"horsemen_{hk}"].append(hv)
        summary = {author: {k: (sum(v)/len(v) if v else 0) for k,v in metrics.items()} for author,metrics in per_author.items()}
        return summary

    metrics_summary = compute_metrics_summary(results)
    
    def compute_timeline(msgs, bins: int = 24):
        if not msgs: return []
        total_len = len(msgs)
        bin_size = max(1, total_len // bins)
        timeline_data = []
        for i in range(0, total_len, bin_size):
            segment = msgs[i:i + bin_size]
            if not segment: continue
            # Simplified: just pass segment for further processing if needed by SVG generator
            # For this prompt, we only need AGG_METRICS mostly.
            # The SVG generators use the more detailed metrics_summary and timeline_data.
            # The LLM needs to refer to AGG_METRICS.
        return [] # Placeholder, actual timeline_data for SVGs computed below

    # Data for programmatic SVGs
    svg_timeline_data = compute_timeline(results, bins=24) # This was compute_timeline, let's keep it
    
    data_pack_for_llm = { # This is AGG_METRICS for the LLM
        "agg_metrics_per_author": metrics_summary,
        # Potentially add more aggregated data if useful for LLM's textual analysis of charts
    }
    metrics_json_for_llm = json.dumps(data_pack_for_llm, ensure_ascii=False, indent=2)

    # Context window limits for settings.META_MODEL (GPT-4-Turbo)
    # GPT-4-Turbo has 128K context. We want to use a good portion for results_json.
    # Budget: META_PROMPT (~3-4K) + metrics_json_for_llm (~1-2K) + quotes_prompt (variable, up to ~5-10K for 200 quotes) + output (4K)
    # Remaining for results_json: 128K - 4K - 2K - 10K - 4K = ~108K.
    # Let's target around 50K-80K tokens for results_json to be safe and control costs.
    # $1 budget for whole report. Primary analysis takes some. $0.60-$0.70 for meta.
    # GPT-4-Turbo input $0.01/1K, output $0.03/1K.
    # For $0.65: 0.01 * T_in/1000 + 0.03 * T_out/1000 = 0.65. If T_out=4K -> $0.12. So, 0.01*T_in/1000 = $0.53 => T_in = 53K tokens.
    target_token_budget_for_results = 50000 # Target for the results_json string

    def strip_bulky_fields(msg_list):
        cleaned = []
        for m_dict in msg_list:
            m_copy = m_dict.copy()
            m_copy.pop("key_quotes", None) # Handled by all_key_quotes and quotes_prompt
            # m_copy.pop("raw", None) # 'raw' might be too bulky if not strictly needed by META_PROMPT themes
            cleaned.append(m_copy)
        return cleaned

    results_to_process_clean = strip_bulky_fields(results)
    temp_results_json = json.dumps(results_to_process_clean, indent=None, ensure_ascii=False)
    estimated_tokens_for_results = estimate_tokens(temp_results_json)

    # Iteratively shrink results_to_process_clean until its JSON representation is under budget
    # MAX_MESSAGES_FOR_META from config (400) is an initial cap before this token-based sampling.
    # This loop further refines based on token budget.
    current_max_messages = settings.MAX_MESSAGES_FOR_META 
    results_to_process_sampled = get_balanced_sample(results_to_process_clean, current_max_messages)
    
    # Minimal sample size if aggressive reduction is needed
    minimal_sample_size_fallback = 200 # User previously set this, let's use it as lower bound for adaptive.

    # Adaptive reduction based on token budget
    while estimate_tokens(json.dumps(results_to_process_sampled, indent=None, ensure_ascii=False)) > target_token_budget_for_results and \
          len(results_to_process_sampled) > minimal_sample_size_fallback:
        current_max_messages = max(minimal_sample_size_fallback, int(len(results_to_process_sampled) * 0.85))
        results_to_process_sampled = get_balanced_sample(results_to_process_clean, current_max_messages) # Sample from the original cleaned full results
        logger.info(f"Adaptive reduction: {len(results_to_process_sampled)} msgs, aiming for <{target_token_budget_for_results} tokens for results_json")

    final_results_json_for_llm = json.dumps(results_to_process_sampled, indent=None, ensure_ascii=False)
    logger.info(f"Final sample size for meta report: {len(results_to_process_sampled)} messages. Estimated tokens for results_json: {estimate_tokens(final_results_json_for_llm)}")

    retry_count = 0
    backoff_time = settings.RETRY_DELAY_SECONDS
    
    tokens_used_meta = 0
    html_content = ""

    while retry_count <= max_retries:
        try:
            quotes_prompt_text = ""
            if all_key_quotes: # Use all_key_quotes extracted from the original full 'results'
                # Limit quotes to avoid excessive prompt length, e.g., max 200 quotes
                quotes_to_include = all_key_quotes[:200]
                quotes_json_for_prompt = json.dumps(quotes_to_include, indent=None, ensure_ascii=False)
                quotes_prompt_text = f"""
                ВАЖНО: Эти {len(quotes_to_include)} ключевых цитат были извлечены из полного анализа. ОБЯЗАТЕЛЬНО интегрируйте их и их анализ в Раздел 5 ("Ключевые цитаты"), даже если они не присутствуют в сокращенной выборке сообщений (`results_json`), которую вы получили.
                {quotes_json_for_prompt}
                """
            
            user_content = (
                f"АНАЛИЗ ЧАТА ДЛЯ ОТЧЕТА:\n"
                f"1. ДАННЫЕ АНАЛИЗА СООБЩЕНИЙ (ВЫБОРКА JSON):\n{final_results_json_for_llm}\n\n"
                f"2. АГРЕГИРОВАННЫЕ МЕТРИКИ (AGG_METRICS JSON):\n{metrics_json_for_llm}\n\n"
                f"3. ДОПОЛНИТЕЛЬНЫЕ КЛЮЧЕВЫЕ ЦИТАТЫ (quotes_prompt):\n{quotes_prompt_text}"
            )

            logger.info(f"Attempting to generate meta report with {settings.META_MODEL}. Input estimate (results_json part): {estimate_tokens(final_results_json_for_llm)} tokens.")
            
            response = await client.chat.completions.create(
                model=settings.META_MODEL,
                messages=[
                    {"role": "system", "content": META_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=4096, # Standard max output, adjust if a different output length is consistently needed
                n=1
            )
            html_content = response.choices[0].message.content
            
            if response.usage:
                tokens_used_meta = response.usage.total_tokens
                # If we need to separate input/output tokens for cost:
                # tokens_input_meta = response.usage.prompt_tokens
                # tokens_output_meta = response.usage.completion_tokens
            else:
                tokens_used_meta = 0 # Fallback

            logger.info(f"Meta report generated. Tokens used: {tokens_used_meta}")
            break # Success

        except openai.RateLimitError as e:
            retry_count += 1
            logger.warning(f"Rate limit exceeded for meta report (attempt {retry_count}/{max_retries}): {e}")
            if retry_count <= max_retries:
                logger.info(f"Retrying meta report in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time) # Use asyncio.sleep
                backoff_time *= 2
                if retry_count == max_retries and len(results_to_process_sampled) > 150: # Last resort reduction
                    results_to_process_sampled = get_balanced_sample(results_to_process_clean, 150)
                    final_results_json_for_llm = json.dumps(results_to_process_sampled, indent=None, ensure_ascii=False)
                    logger.info(f"Final meta attempt with further reduced sample: {len(results_to_process_sampled)} messages.")
            else:
                logger.error("Max retries reached for meta report generation due to rate limits.")
                html_content = _generate_error_html(str(e), "Rate limit error after multiple retries.")
                return html_content, 0
        
        except openai.OpenAIError as e: # Catch other OpenAI errors
            logger.error(f"OpenAI API error during meta report generation: {e}")
            if "context_length_exceeded" in str(e).lower():
                logger.warning("Context length exceeded for meta report. Trying with minimal sample.")
                # This logic might need to be more robust, potentially reducing target_token_budget_for_results further
                # or using an even smaller minimal_sample_size_fallback for this specific error.
                # For now, the loop for adaptive reduction should handle this if it's systematically too large.
                # If it happens *after* sampling, it means the prompt + sampled data is still too big.
                # Fallback to error HTML for now if this specific error is not resolved by retries or sampling.
                html_content = _generate_error_html(str(e), "Context length exceeded.")
                return html_content, 0 # Bail out on context length errors not caught by sampling

            # Generic retry for other API errors
            retry_count += 1
            if retry_count <= max_retries:
                logger.info(f"Retrying meta report due to API error in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2
            else:
                logger.error("Max retries reached for meta report generation due to API errors.")
                html_content = _generate_error_html(str(e), "API error after multiple retries.")
                return html_content, 0
        except Exception as e: # Catch any other unexpected error
            logger.exception(f"Unexpected error during meta report generation: {e}")
            html_content = _generate_error_html(str(e), "An unexpected error occurred.")
            return html_content, 0


    # Post-processing HTML
    if html_content:
        # --- Inject additional CSS for better readability ---
        def _inject_css(html_str: str) -> str:
            import re
            style_block = """
            <style>
                body { font-size: 16px; line-height: 1.7; } /* Adjusted for typical screen reading */
                h1 { font-size: 28px; margin-bottom: 25px; }
                h2 { font-size: 22px; margin-top: 35px; margin-bottom: 15px; }
                h3 { font-size: 18px; margin-top: 25px; margin-bottom: 10px; }
                svg text { font-family: Arial, sans-serif; font-size: 12px; } /* Smaller SVG text */
                .quote { border-left: 4px solid #3498db; padding: 10px 15px; margin: 20px 0; background-color: #f8f9fa; }
                .quote p { margin: 5px 0; }
                .quote-author { font-weight: bold; color: #555; }
                .quote-emotion { color: #777; font-size: 0.9em; }
                .chart-container { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 25px 0; overflow-x: auto; } /* Added container for charts */
            </style>
            """
            head_match = re.search(r"<head[^>]*>", html_str, re.IGNORECASE)
            if head_match:
                insert_pos = head_match.end()
                return html_str[:insert_pos] + style_block + html_str[insert_pos:]
            return style_block + html_str # Fallback if no head tag

        html_content = _inject_css(html_content)

        import html as _html_module
        html_content = _html_module.unescape(html_content)

        import re
        leading_html_match = re.search(r'(<!DOCTYPE html[\s\S]*|<html[\s\S]*)', html_content, re.IGNORECASE)
        if leading_html_match:
            html_content = leading_html_match.group(1).lstrip()
        
        _html_start = html_content.lstrip()[:40].lower()
        if not (_html_start.startswith("<!doctype html") or _html_start.startswith("<html")):
            logger.warning("Meta report output doesn't seem to start with valid HTML doctype/tag. Wrapping it.")
            # This basic wrapper might be too simple if the LLM produced partial HTML or just text.
            # The prompt strongly guides for full HTML.
            html_content = f"""<!DOCTYPE html>
                            <html><head><meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Chat X-Ray: Психологический анализ отношений</title></head><body>
                            <h1>Отчет (Возможно, неполный)</h1><div>{html_content}</div></body></html>"""

        if "<meta name=\"viewport\"" not in html_content:
            html_content = html_content.replace("<head>", "<head>\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">", 1)
            
        # Add sampling disclaimer if applicable
        # results_to_process_sampled is the actual data sent to LLM. 'results' is the full primary analysis.
        if len(results_to_process_sampled) < len(results_to_process_clean): # Compare sampled vs full cleaned list
            import re
            body_pattern = r'<body[^>]*>'
            disclaimer_text = f"""
            <div style="background-color: #fff3cd; color: #856404; padding: 15px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #ffeeba;">
                <strong>Примечание о выборке:</strong> Этот анализ основан на автоматически отобранной выборке из {len(results_to_process_sampled)} проанализированных сегментов сообщений 
                (из общего числа {len(results_to_process_clean)} доступных сегментов после первичной обработки {len(results)} исходных сообщений).
                Выборка стремится охватить начало, середину и конец чата для сбалансированного анализа в рамках установленного бюджета.
            </div>
            """
            if re.search(body_pattern, html_content):
                html_content = re.sub(body_pattern, lambda m: m.group(0) + disclaimer_text, html_content, count=1)
            else:
                html_content = disclaimer_text + html_content

        msg_banner = (
            f"""
            <div style=\"background-color:#e8f4fd; color: #1e4271; padding:12px; margin-bottom:20px; border-left:4px solid #3498db;\">
                Отчёт подготовлен после анализа <b>{total_messages}</b> сообщений из вашего чата.
            </div>
            """
        )
        body_tag_re = re.compile(r"<body[^>]*>", re.IGNORECASE)
        html_content, subs = body_tag_re.subn(lambda m: m.group(0)+msg_banner, html_content, count=1)
        if subs == 0: html_content = msg_banner + html_content
        
        # ---- Programmatically generate SVG charts ----
        try:
            svgs_to_inject: List[str] = []
            # Ensure metrics_summary and svg_timeline_data are available and correct for these functions
            
            # 1. Sentiment timeline (svg_timeline_data needs to be correctly computed for this)
            # The compute_timeline was simplified; let's assume graphics.py can handle raw segments or needs specific format.
            # For now, let's rely on data within metrics_summary for other charts if timeline is too complex to quickly re-integrate.
            # svgs_to_inject.append(generate_sentiment_timeline_svg(svg_timeline_data)) # This needs correctly formatted svg_timeline_data

            # 2. Radar chart of core metrics per author
            if metrics_summary: svgs_to_inject.append(generate_radar_chart_svg(metrics_summary))

            # 3. Bar chart of overall toxicity per author
            toxicity_totals = {a: round(m.get("toxicity",0),3) for a,m in metrics_summary.items() if m}
            if toxicity_totals: svgs_to_inject.append(generate_bar_chart_svg(toxicity_totals, "Средний уровень токсичности по авторам", chart_id="chart-toxicity"))

            manip_totals = {a: round(m.get("manipulation",0),3) for a,m in metrics_summary.items() if m}
            if manip_totals: svgs_to_inject.append(generate_bar_chart_svg(manip_totals, "Уровень манипулятивности по авторам", chart_id="chart-manipulation"))
            
            assert_totals = {a: round(m.get("assertiveness",0),3) for a,m in metrics_summary.items() if m}
            if assert_totals: svgs_to_inject.append(generate_bar_chart_svg(assert_totals, "Уровень ассертивности по авторам", chart_id="chart-assertiveness"))

            empathy_totals = {a: round(m.get("empathy",0),3) for a,m in metrics_summary.items() if m}
            if empathy_totals: svgs_to_inject.append(generate_bar_chart_svg(empathy_totals, "Уровень эмпатии по авторам", chart_id="chart-empathy"))

            horsemen_overall = defaultdict(float)
            for author_metrics in metrics_summary.values():
                for key, value in author_metrics.items():
                    if key.startswith("horsemen_"):
                        horsemen_overall[key.replace("horsemen_","").capitalize()] += value
            if horsemen_overall:
                avg_horsemen = {k: round(v / len(metrics_summary) if metrics_summary else 0, 3) for k,v in horsemen_overall.items()}
                svgs_to_inject.append(generate_bar_chart_svg(avg_horsemen, "Среднее проявление \"Всадников Апокалипсиса\"", chart_id="chart-horsemen"))

            chart_container_template = "<div class='chart-container'>{}</div>"
            for svg_code in svgs_to_inject:
                styled_svg = chart_container_template.format(svg_code)
                # Replace placeholders sequentially. Ensure META_PROMPT asks for these placeholders.
                html_content = re.sub(r'<p class="chart-placeholder">[\s\S]*?</p>', styled_svg, html_content, count=1)
            
            # Remove any remaining placeholders if not enough SVGs were generated
            html_content = re.sub(r'<p class="chart-placeholder">[\s\S]*?</p>', '<p><i>(Визуализация для этого раздела не была сгенерирована.)</i></p>', html_content)

        except Exception as gerr:
            logger.warning(f"Programmatic SVG injection failed: {gerr}", exc_info=True)

    return html_content, tokens_used_meta

def _generate_error_html(error_message: str, details: str = "") -> str:
    # Sanitize error_message for HTML display
    import html as _html_module
    safe_error_message = _html_module.escape(error_message)
    safe_details = _html_module.escape(details)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Chat X-Ray: Ошибка отчета</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: auto; padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; }}
            h1 {{ color: #d9534f; text-align: center; }}
            .error-box {{ background-color: #f2dede; color: #a94442; padding: 15px; border-radius: 5px; border: 1px solid #ebccd1; margin-bottom: 20px; }}
            .error-box strong {{ font-size: 1.1em; }}
            .suggestion {{ background-color: #d9edf7; color: #31708f; padding: 15px; border-radius: 5px; border: 1px solid #bce8f1; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ошибка при создании отчета</h1>
            <div class="error-box">
                <p><strong>При анализе вашего чата произошла критическая ошибка:</strong></p>
                <p>{safe_details}</p>
                <p><i>Детали ошибки: {safe_error_message}</i></p>
                <p>Пожалуйста, попробуйте еще раз позже. Если проблема не исчезнет, возможно, чат слишком большой или имеет необычный формат.</p>
            </div>
            <div class="suggestion">
                <p><strong>Возможные быстрые решения:</strong></p>
                <ul>
                    <li>Попробуйте загрузить файл меньшего размера (например, часть текущего чата).</li>
                    <li>Убедитесь, что файл содержит текстовые сообщения в стандартном формате (например, экспорт из WhatsApp или Telegram).</li>
                    <li>Попробуйте снова через несколько минут, возможно, это была временная проблема с сервисом анализа.</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """ 