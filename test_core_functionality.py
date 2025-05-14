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
    # Use the sample chat file
    sample_file_path = Path("sample_chat.txt")
    
    if not sample_file_path.exists():
        print(f"Error: Sample file {sample_file_path} not found")
        return
    
    # Make sure output directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    
    print(f"Processing sample chat file: {sample_file_path}")
    
    # Generate unique IDs for the files
    file_id = "test_run"
    report_file_path = settings.REPORT_DIR / f"{file_id}.pdf"
    html_file_path = settings.REPORT_DIR / f"{file_id}.html"
    
    try:
        print("Step 1: Splitting chat into chunks...")
        chunks = split_chat(sample_file_path)
        num_chunks = len(chunks)
        print(f"  - Split into {num_chunks} chunks")
        
        # Check if we're dealing with a very large chat that might hit rate limits
        total_messages = sum(len(chunk) for chunk in chunks)
        if total_messages > 1000:
            print(f"  ⚠️ Warning: Large chat detected ({total_messages} messages)")
            print("  - Using reduced sampling to avoid rate limits")
            # Sampling would be implemented in the actual services
        
        print("\nStep 2: Processing chunks with GPT-3.5 Turbo...")
        try:
            analysis_results = await process_chunks(chunks)
            print(f"  - Processed {len(analysis_results)} messages")
        except openai.RateLimitError as e:
            print(f"  ❌ Rate limit exceeded during analysis: {e}")
            print("  - Try processing fewer messages or waiting and trying again later")
            return
        
        print("\nStep 3: Generating meta report with GPT-4...")
        try:
            html_content = await generate_meta_report(analysis_results)
            print("  - Generated HTML report")
            
            # Save HTML content to file
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"  - Saved HTML to {html_file_path}")
        except openai.RateLimitError as e:
            print(f"  ❌ Rate limit exceeded during meta analysis: {e}")
            print("  - Saving intermediate results to avoid losing progress")
            
            # If we hit rate limits, save what we've got so far
            with open(settings.REPORT_DIR / f"{file_id}_partial.json", "w", encoding="utf-8") as f:
                import json
                json.dump(analysis_results, f, indent=2)
            print(f"  - Saved partial results to {settings.REPORT_DIR / f'{file_id}_partial.json'}")
            return
        
        print("\nStep 4: Rendering HTML to PDF...")
        try:
            pdf_url = await render_to_pdf(html_file_path, report_file_path)
            print(f"  - PDF available at: {pdf_url}")
        except Exception as e:
            print(f"  ⚠️ Error rendering PDF: {e}")
            print("  - HTML report is still available")
        
        # Log approximate cost
        approx_cost = (num_chunks * 0.0005) + 0.01  # $0.0005 per chunk for GPT-3.5 + $0.01 for GPT-4 Turbo
        await log_cost("test_user", num_chunks, approx_cost)
        print(f"\nApproximate cost: ${approx_cost:.4f}")
        
        print("\nProcess completed successfully!")
        print(f"View the PDF report at: {report_file_path}")
        
    except openai.RateLimitError as e:
        print(f"\n❌ Rate limit error: {e}")
        print("This usually happens when your chat is very large or we're processing many requests.")
        print("Suggestions:")
        print("  1. Try processing a smaller chat file")
        print("  2. Wait for a few minutes and try again")
        print("  3. Check your OpenAI API usage limits and quotas")
        
    except openai.AuthenticationError as e:
        print(f"\n❌ Authentication error: {e}")
        print("Please check your OpenAI API key in the .env file")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(0) 