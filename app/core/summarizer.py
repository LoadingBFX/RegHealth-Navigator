"""
summarizer.py

Summary Generator for CMS regulatory rules using OpenAI.
Provides comprehensive document summarization with batch processing and caching.

Functionality:
- Chunk-based summarization using OpenAI GPT-4o-mini
- Batch processing with async concurrency control
- Intelligent caching to reduce API costs
- Token management and context optimization
- Final report synthesis with action items
- Support for large documents with segmentation

Process Flow:
1. Load document chunks from RAG system
2. Split chunks into manageable batches
3. Process batches concurrently with rate limiting
4. Cache batch results to avoid redundant API calls
5. Synthesize final executive summary
6. Handle large documents with automatic segmentation
7. Save results as Markdown files

Author: Seon
"""

import os
import json
import sys
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI, AsyncOpenAI

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
try:
    from ..config import config
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    # Add parent directory to path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from config import config


class SummaryGenerator:
    """
    Summary Generator for CMS regulatory rules using OpenAI.
    
    Responsibilities:
    - Chunk-based summarization using LLM
    - Topic extraction with metadata (key changes, stakeholders, data)
    - Final report synthesis with action items

    Usage:
        generator = SummaryGenerator()
        generator.generate_report(chunk_data, file_name)
    """

    def __init__(self, output_dir: str = None, openai_api_key: str = os.getenv("OPENAI_API_KEY"), use_async: bool = True, batch_size: int = 20):
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.async_client = AsyncOpenAI(api_key=openai_api_key) if use_async else None
        self.use_async = use_async
        self.batch_size = batch_size
        # Use config for output directory if not provided
        if output_dir is None:
            output_dir = config.summary_output_dir
        
        self.summary_dir = Path(output_dir)
        self.summary_dir.mkdir(exist_ok=True)

    def _count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """Count tokens accurately using tiktoken if available, fallback to estimation."""
        if TIKTOKEN_AVAILABLE:
            try:
                # encoding = tiktoken.encoding_for_model(model)
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception as e:
                print(f"⚠️ Tiktoken failed, using estimation: {e}")
        
        # Fallback estimation (rough approximation)
        return len(text.encode("utf-8")) // 4

    def _chunk_batches(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
    
    def _get_batch_hash(self, batch: List[Dict]) -> str:
        """Generate hash for batch content to use as cache key."""
        batch_text = "\n".join(
            c.get('page_content', '') or c.get('text', '') for c in batch
        )
        return hashlib.md5(batch_text.encode('utf-8')).hexdigest()
    
    def _get_batch_cache_path(self, file_name: str, batch_idx: int, batch_hash: str) -> Path:
        """Get cache path for a specific batch."""
        cache_dir = self.summary_dir / "batch_cache" / file_name
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"batch_{batch_idx}_{batch_hash}.json"
    
    def _get_batch_index_path(self, file_name: str) -> Path:
        """Get path for batch processing index file."""
        cache_dir = self.summary_dir / "batch_cache" / file_name
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "batch_index.json"
    
    def _load_batch_cache(self, file_name: str) -> Dict:
        """Load batch processing index."""
        index_path = self._get_batch_index_path(file_name)
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading batch index: {e}")
        return {"batches": {}, "completed": False}
    
    def _save_batch_cache(self, file_name: str, batch_idx: int, batch_hash: str, result: List[Dict]):
        """Save batch result to cache."""
        try:
            # Save batch result
            cache_path = self._get_batch_cache_path(file_name, batch_idx, batch_hash)
            with open(cache_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Update index
            index_data = self._load_batch_cache(file_name)
            index_data["batches"][str(batch_idx)] = {
                "hash": batch_hash,
                "cache_file": cache_path.name,
                "result_count": len(result),
                "timestamp": str(Path().stat().st_mtime)
            }
            
            index_path = self._get_batch_index_path(file_name)
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error saving batch cache: {e}")
    
    def _get_cached_batch_result(self, file_name: str, batch_idx: int, batch_hash: str) -> List[Dict]:
        """Get cached result for a batch if available."""
        try:
            cache_path = self._get_batch_cache_path(file_name, batch_idx, batch_hash)
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading cached batch: {e}")
        return []
    
    async def _process_batch_async(self, program: str, batch: List[Dict], batch_idx: int, file_name: str, batch_hash: str) -> List[Dict]:
        """Process a single batch asynchronously."""
        try:
            prompt = self._get_batch_prompt(program, batch, batch_idx + 1)
            
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            parsed = json.loads(response.choices[0].message.content)
            if isinstance(parsed, list):
                batch_result = parsed
            else:
                batch_result = [parsed]
            
            # Cache the batch result
            self._save_batch_cache(file_name, batch_idx, batch_hash, batch_result)
            print(f"✅ Batch {batch_idx + 1} summarized and cached (async).")
            return batch_result
            
        except Exception as e:
            print(f"❌ Error summarizing batch {batch_idx + 1} (async): {e}")
            return []
    
    def _process_batch_sync(self, program: str, batch: List[Dict], batch_idx: int, file_name: str, batch_hash: str) -> List[Dict]:
        """Process a single batch synchronously."""
        try:
            prompt = self._get_batch_prompt(program, batch, batch_idx + 1)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            parsed = json.loads(response.choices[0].message.content)
            if isinstance(parsed, list):
                batch_result = parsed
            else:
                batch_result = [parsed]
            
            # Cache the batch result
            self._save_batch_cache(file_name, batch_idx, batch_hash, batch_result)
            print(f"✅ Batch {batch_idx + 1} summarized and cached (sync).")
            return batch_result
            
        except Exception as e:
            print(f"❌ Error summarizing batch {batch_idx + 1} (sync): {e}")
            return []
    
    async def _process_batches_async(self, program: str, batches: List[List[Dict]], file_name: str) -> List[Dict]:
        """Process multiple batches concurrently with rate limiting."""
        individual_summaries = []
        
        # Process batches with concurrency control
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests to avoid rate limits
        
        async def process_batch_with_semaphore(batch_idx, batch):
            async with semaphore:
                batch_hash = self._get_batch_hash(batch)
                
                # Check if batch is cached
                cached_result = self._get_cached_batch_result(file_name, batch_idx, batch_hash)
                if cached_result:
                    print(f"📄 Using cached result for batch {batch_idx + 1}/{len(batches)}")
                    return cached_result
                
                print(f"🔄 Summarizing batch {batch_idx + 1}/{len(batches)} (async)...")
                return await self._process_batch_async(program, batch, batch_idx, file_name, batch_hash)
        
        # Create tasks for all batches
        tasks = [process_batch_with_semaphore(i, batch) for i, batch in enumerate(batches)]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Batch {i + 1} failed with exception: {result}")
            elif result:
                individual_summaries.extend(result)
        
        return individual_summaries

    def _get_batch_prompt(self, program: str, batch: List[Dict], batch_num: int) -> str:
        formatted = "\n\n".join(
            f"[Section {i + 1}]\n{c.get('page_content') or c.get('text', '')}" for i, c in enumerate(batch)
        )
        return f"""
                You are a senior compliance analyst reviewing CMS {program.upper()} Final Rule content.

                Below are multiple sections grouped together. For each distinct topic you identify in the text, extract:
                - topic (brief title)
                - key_changes (bulleted list with conditions, expiration dates, etc.)
                - quantitative_data (numbers, percentages, codes, dates)
                - stakeholders_affected (e.g. physicians, billing staff)

                Respond as a list of valid JSON objects.

                [Start of batched text: Batch {batch_num}]
                {formatted}
                [End of text]
                """

    def _get_final_report_prompt(self, program: str, year: str, summaries: str) -> str:
        try:
            parsed = json.loads(summaries)
            unique_topics = sorted(set(s.get("topic", "").strip() for s in parsed if s.get("topic")))
            section_str = "\n".join(f"- {t}" for t in unique_topics if t)
        except Exception:
            section_str = "- Key Policy Changes"

        title = f"Business Intelligence Report: CY {year} {program.upper()} Final Rule"
        return f"""
                You are a senior regulatory analyst. Using the structured JSON below, write a professional summary for executives.

                ### {title}

                **Sections to include:**
                {section_str}
                - Action Items for Stakeholders

                Use specific numbers, dates, and codes. Emphasize what is temporary vs. permanent.

                [Start of structured JSON data]
                {summaries}
                [End of structured JSON data]
                """

    def generate_report(self, chunks_data: List[Dict], file_name: str) -> str:
        program = "MPFS"
        lower_name = file_name.lower()
        if "hospice" in lower_name:
            program = "Hospice"
        elif "snf" in lower_name:
            program = "SNF"

        summary_path = self.summary_dir / f"{file_name}.md"
        json_path = self.summary_dir / f"{file_name}.json"

        if summary_path.exists():
            print("📄 Cached summary found. Loading...\n")
            return summary_path.read_text()

        # Check for batch cache first
        batch_cache = self._load_batch_cache(file_name)
        if batch_cache.get("completed", False):
            print("📄 Found completed batch cache, loading all results...")
            individual_summaries = []
            for batch_idx, batch_info in batch_cache["batches"].items():
                cache_path = self.summary_dir / "batch_cache" / file_name / batch_info["cache_file"]
                if cache_path.exists():
                    with open(cache_path, 'r') as f:
                        batch_result = json.load(f)
                        individual_summaries.extend(batch_result)
            print(f"📄 Loaded {len(individual_summaries)} summaries from cache")
        elif json_path.exists():
            print("📄 Found precomputed JSON summary.")
            with open(json_path, 'r') as jf:
                individual_summaries = json.load(jf)
        else:
            individual_summaries = []
            batches = self._chunk_batches(chunks_data, batch_size=self.batch_size)
            print(f"📄 Processing {len(batches)} batches with caching...")

            if self.use_async and self.async_client:
                # Use async processing
                print("🚀 Using async processing for faster batch handling...")
                individual_summaries = asyncio.run(self._process_batches_async(program, batches, file_name))
            else:
                # Use sync processing
                print("🔄 Using synchronous processing...")
                for b_idx, batch in enumerate(batches):
                    batch_hash = self._get_batch_hash(batch)
                    
                    # Check if batch is cached
                    cached_result = self._get_cached_batch_result(file_name, b_idx, batch_hash)
                    if cached_result:
                        print(f"📄 Using cached result for batch {b_idx + 1}/{len(batches)}")
                        individual_summaries.extend(cached_result)
                        continue
                    
                    batch_result = self._process_batch_sync(program, batch, b_idx, file_name, batch_hash)
                    if batch_result:
                        individual_summaries.extend(batch_result)

            if not individual_summaries:
                return "No report generated; all batch analysis failed."

            # Mark as completed and save combined JSON
            batch_cache["completed"] = True
            index_path = self._get_batch_index_path(file_name)
            with open(index_path, 'w') as f:
                json.dump(batch_cache, f, indent=2)
            
            with open(json_path, 'w') as jf:
                json.dump(individual_summaries, jf, indent=2)
            print(f"💾 Intermediate JSON saved to {json_path}")

        year_str = file_name.split('_')[0] if '_' in file_name else "latest"
        
        # Check token count and handle large summaries
        token_count = self._count_tokens(json.dumps(individual_summaries, indent=2))
        max_tokens = 128000 - 16384  # 111616
        
        if token_count > max_tokens:
            print(f"⚠️ Summary data is large ({token_count} tokens), using segmented approach...")
            final_report = self._generate_segmented_final_report(program, year_str, individual_summaries)
        else:
            final_report = self._generate_single_final_report(program, year_str, individual_summaries)
        
        # Save final report
        with open(summary_path, 'w') as f:
            f.write(final_report)
        print("✅ Final report saved.")
        return final_report
    
    def _generate_single_final_report(self, program: str, year: str, summaries: List[Dict]) -> str:
        """Generate final report in a single API call."""
        try:
            joined_summaries = json.dumps(summaries, indent=2)
            final_prompt = self._get_final_report_prompt(program, year, joined_summaries)
            
            print("\n🔄 Generating final summary report...")
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.1,
            )
            return final_response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Error generating single final report: {e}")
            return f"Final synthesis failed. Raw data below:\n\n{json.dumps(summaries, indent=2)}"
    
    async def _process_segment_async(self, program: str, chunk: List[Dict], segment_idx: int, total_segments: int) -> str:
        """Process a single segment asynchronously."""
        try:
            chunk_json = json.dumps(chunk, indent=2)
            segment_prompt = f"""
            You are a senior regulatory analyst. Create a concise executive summary for this segment of CMS {program.upper()} Final Rule data.
            
            Focus on the most important changes, key stakeholders affected, and critical action items.
            Use specific numbers, dates, and codes where available.
            
            [Segment {segment_idx + 1} of {total_segments}]
            {chunk_json}
            """
            
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": segment_prompt}],
                temperature=0.1,
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error processing segment {segment_idx + 1} (async): {e}")
            return f"[Segment {segment_idx + 1} processing failed]"
    
    async def _generate_segmented_final_report_async(self, program: str, year: str, summaries: List[Dict]) -> str:
        """Generate final report using segmented approach with async processing."""
        try:
            print("\n🔄 Generating segmented final summary report (async)...")
            
            # Split summaries into manageable chunks
            chunk_size = 20  # Number of summaries per chunk
            summary_chunks = [summaries[i:i + chunk_size] for i in range(0, len(summaries), chunk_size)]
            
            # Process segments concurrently
            semaphore = asyncio.Semaphore(2)  # Limit concurrent requests for final report
            
            async def process_segment_with_semaphore(segment_idx, chunk):
                async with semaphore:
                    print(f"🔄 Processing summary segment {segment_idx + 1}/{len(summary_chunks)} (async)...")
                    return await self._process_segment_async(program, chunk, segment_idx, len(summary_chunks))
            
            # Create tasks for all segments
            tasks = [process_segment_with_semaphore(i, chunk) for i, chunk in enumerate(summary_chunks)]
            
            # Execute all tasks concurrently
            partial_summaries = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            processed_summaries = []
            for i, result in enumerate(partial_summaries):
                if isinstance(result, Exception):
                    print(f"❌ Segment {i + 1} failed with exception: {result}")
                    processed_summaries.append(f"[Segment {i + 1} processing failed]")
                else:
                    processed_summaries.append(result)
            
            # Combine partial summaries into final report
            combined_summaries = "\n\n".join(processed_summaries)
            final_prompt = f"""
            You are a senior regulatory analyst. Create a comprehensive executive summary by combining these partial summaries.
            
            ### Business Intelligence Report: CY {year} {program.upper()} Final Rule
            
            **Instructions:**
            - Synthesize the partial summaries into a coherent executive report
            - Maintain all important details, numbers, and action items
            - Organize by key themes and stakeholder impacts
            - Include a clear executive summary at the beginning
            
            [Combined partial summaries]
            {combined_summaries}
            """
            
            final_response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.1,
            )
            return final_response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating segmented final report (async): {e}")
            return f"Segmented final synthesis failed. Raw data below:\n\n{json.dumps(summaries, indent=2)}"
    
    def _generate_segmented_final_report(self, program: str, year: str, summaries: List[Dict]) -> str:
        """Generate final report using segmented approach for large datasets."""
        try:
            print("\n🔄 Generating segmented final summary report...")
            
            # Use async if available, otherwise fall back to sync
            if self.use_async and self.async_client:
                return asyncio.run(self._generate_segmented_final_report_async(program, year, summaries))
            
            # Fallback to sync processing
            # Split summaries into manageable chunks
            chunk_size = 20  # Number of summaries per chunk
            summary_chunks = [summaries[i:i + chunk_size] for i in range(0, len(summaries), chunk_size)]
            
            # Generate partial summaries for each chunk
            partial_summaries = []
            for i, chunk in enumerate(summary_chunks):
                print(f"🔄 Processing summary segment {i + 1}/{len(summary_chunks)}...")
                
                chunk_json = json.dumps(chunk, indent=2)
                segment_prompt = f"""
                You are a senior regulatory analyst. Create a concise executive summary for this segment of CMS {program.upper()} Final Rule data.
                
                Focus on the most important changes, key stakeholders affected, and critical action items.
                Use specific numbers, dates, and codes where available.
                
                [Segment {i + 1} of {len(summary_chunks)}]
                {chunk_json}
                """
                
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": segment_prompt}],
                        temperature=0.1,
                    )
                    partial_summaries.append(response.choices[0].message.content.strip())
                except Exception as e:
                    print(f"❌ Error processing segment {i + 1}: {e}")
                    partial_summaries.append(f"[Segment {i + 1} processing failed]")
            
            # Combine partial summaries into final report
            combined_summaries = "\n\n".join(partial_summaries)
            final_prompt = f"""
            You are a senior regulatory analyst. Create a comprehensive executive summary by combining these partial summaries.
            
            ### Business Intelligence Report: CY {year} {program.upper()} Final Rule
            
            **Instructions:**
            - Synthesize the partial summaries into a coherent executive report
            - Maintain all important details, numbers, and action items
            - Organize by key themes and stakeholder impacts
            - Include a clear executive summary at the beginning
            
            [Combined partial summaries]
            {combined_summaries}
            """
            
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.1,
            )
            return final_response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating segmented final report: {e}")
            return f"Segmented final synthesis failed. Raw data below:\n\n{json.dumps(summaries, indent=2)}"
