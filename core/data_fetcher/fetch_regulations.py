#!/usr/bin/env python3
import argparse
import logging
import time
import random
import requests
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

def setup_logging(verbose: bool = False):
    """Configure logging with both console and file handlers."""
    log_dir = Path('log')
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'regulation_fetch.log'
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_latest_documents(days: int = 365) -> List[Dict]:
    """Get latest documents from Federal Register API."""
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # API 参数
    params = {
        'conditions[type][]': ['RULE', 'PRORULE'],
        'conditions[agencies][]': ['centers-for-medicare-medicaid-services'],
        'order': 'newest',
        'per_page': 100,
        'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
        'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d')
    }
    
    # 设置请求头
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            'https://www.federalregister.gov/api/v1/documents.json',
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except Exception as e:
        print(f"Error fetching document list: {str(e)}")
        return []

def should_skip_document(doc: Dict) -> tuple[bool, str]:
    """Check if a document should be skipped."""
    # 跳过未来日期的文档
    pub_date = datetime.strptime(doc.get('publication_date'), '%Y-%m-%d')
    if pub_date > datetime.now():
        return True, f"Future document ({doc.get('publication_date')})"
    
    # 跳过修订文档（C1-, C2-, etc.）
    doc_number = doc.get('document_number', '')
    if doc_number.startswith('C'):
        return True, f"Correction document ({doc_number})"
    
    
    return False, ""

def detect_program_type(doc: Dict) -> tuple[bool, str]:
    """
    Detect program type from document title.
    
    Args:
        doc (Dict): Document data from API
        
    Returns:
        tuple[bool, str]: (是否识别到程序类型, 程序类型)
    """
    title = doc.get('title', '').lower()
    
    # 定义程序类型及其关键词
    program_keywords = {
        'MPFS': ['physician fee schedule', 'mpfs', 'pfs'],
        'HOSPICE': ['hospice wage', 'hospice payment', 'hospice quality'],
        'SNF': ['skilled nursing facility', 'snf', 'nursing facility']
    }
    
    # 检查每个程序类型的关键词
    for program_type, keywords in program_keywords.items():
        if any(keyword in title for keyword in keywords):
            return True, program_type
            
    return False, 'UNCLASSIFIED'

def get_document_filename(doc: Dict) -> str:
    """Generate standardized filename for a document."""
    doc_number = doc.get('document_number', '')
    doc_type = doc.get('type', '').lower()
    pub_date = datetime.strptime(doc.get('publication_date'), '%Y-%m-%d')
    year = pub_date.strftime('%Y')
    
    # 获取程序类型
    has_program, program_type = detect_program_type(doc)
    
    # 规范化文档类型
    if doc_type == 'rule':
        doc_type = 'final'
    elif doc_type == 'prorule':
        doc_type = 'proposed'
    else:
        doc_type = 'other'
    
    # 生成文件名：年份_程序类型_类型_原始文档号.xml
    return f"{year}_{program_type}_{doc_type}_{doc_number}.xml"

def download_xml(doc: Dict, save_dir: Path, logger=None) -> bool:
    """Download XML file using the verified URL format."""
    doc_number = doc.get('document_number')
    pub_date = datetime.strptime(doc.get('publication_date'), '%Y-%m-%d')
    year = pub_date.strftime('%Y')
    month = pub_date.strftime('%m')
    day = pub_date.strftime('%d')
    
    # 构建 URL
    url = f"https://www.federalregister.gov/documents/full_text/xml/{year}/{month}/{day}/{doc_number}.xml"
    
    # 设置浏览器样式的请求头
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

    try:
        # 发送请求
        response = requests.get(url, headers=headers, timeout=30)
        
        # 检查响应
        if response.status_code == 200:
            # 检查是否是有效的 XML
            content = response.content
            if (b"<?xml" in content[:100] or 
                b"<NOTICE>" in content[:100] or 
                b"<RULE>" in content[:100] or 
                b"<PRORULE>" in content[:100]):
                # 生成标准文件名
                filename = get_document_filename(doc)
                save_path = save_dir / filename
                
                # 直接保存为标准文件名
                save_path.write_bytes(content)
                if logger:
                    logger.info(f"✅ Successfully downloaded: {save_path}")
                return True
            else:
                if logger:
                    logger.warning(f"❌ Invalid XML content for {doc_number}")
                return False
        else:
            if logger:
                logger.warning(f"❌ Failed to download {doc_number}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        if logger:
            logger.error(f"❌ Error downloading {doc_number}: {str(e)}")
        return False

def process_document(doc: Dict, save_dir: Path, logger=None) -> tuple[bool, str]:
    """Process a single document."""
    doc_number = doc.get('document_number')
        
    # 检查是否应该跳过
    skip, reason = should_skip_document(doc)
    if skip:
        if logger:
            logger.info(f"Skip {doc_number}: {reason}")
        return False, reason
    
    # 检查程序类型
    has_program, program_type = detect_program_type(doc)
    if not has_program:
        if logger:
            logger.info(f"Unrecognized program type: {doc.get('title')}")
        return False, f"Unrecognized program type: {doc.get('title')}"
    
    # 检查文档类型
    doc_type = doc.get('type', '').lower()
    if doc_type not in ['rule', 'prorule']:
        if logger:
            logger.info(f"Unsupported document type: {doc_type}")
        return False, f"Unsupported document type: {doc_type}"
    
    # 创建程序类型目录
    program_dir = save_dir / program_type
    program_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成标准文件名
    filename = get_document_filename(doc)
    save_path = program_dir / filename
    
    # 检查文件是否已存在
    if save_path.exists():
        if logger:
            logger.info(f"Already exists: {save_path}")
        return True, f"Already exists: {save_path}"
    
    # 下载文件
    success = download_xml(doc, program_dir, logger=logger)
    if success:
        return True, f"Successfully downloaded: {save_path}"
    else:
        return False, f"Failed to download: {doc_number}"

def get_single_document(doc_number: str) -> Optional[Dict]:
    """Get a single document by document number."""
    url = f"https://www.federalregister.gov/api/v1/documents/{doc_number}.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching document: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Federal Register document fetcher')
    parser.add_argument('--mode', choices=['single', 'latest'], default='latest',
                      help='Operation mode: single (one document) or latest (fetch latest documents)')
    parser.add_argument('--doc-number', type=str,
                      help='Document number to download (e.g., 2024-06431)')
    parser.add_argument('--date', type=str,
                      help='Publication date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=365,
                      help='Number of days to look back (for latest mode)')
    parser.add_argument('--output-dir', type=str, default='data',
                      help='Output directory for downloaded files')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    
    try:
        # 创建输出目录
        save_dir = Path(args.output_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        if args.mode == 'single':
            if not args.doc_number:
                logger.error("❌ Error: --doc-number is required for single mode")
                sys.exit(1)
            
            # 获取文档信息
            doc = get_single_document(args.doc_number)
            if not doc:
                logger.error(f"❌ Error: Document {args.doc_number} not found")
                sys.exit(1)
            
            # 处理文档
            success, message = process_document(doc, save_dir, logger=logger)
            logger.info(message)
            if not success:
                sys.exit(1)
                
        elif args.mode == 'latest':
            logger.info(f"Fetching latest documents from the past {args.days} days...")
            documents = get_latest_documents(args.days)
            logger.info(f"Found {len(documents)} documents")
            
            successful = 0
            failed = 0
            skipped = 0
            unrecognized = 0
            unsupported = 0
            
            for doc in documents:
                success, message = process_document(doc, save_dir, logger=logger)
                logger.info(f"{doc.get('document_number')}: {message}")
                
                if success:
                    successful += 1
                elif "Already exists" in message:
                    skipped += 1
                elif "Unrecognized program type" in message:
                    unrecognized += 1
                elif "Unsupported document type" in message:
                    unsupported += 1
                else:
                    failed += 1
                
                # 随机延迟，避免请求过快
                time.sleep(random.uniform(2, 5))
            
            logger.info(f"\nDownload Summary:")
            logger.info(f"Total documents: {len(documents)}")
            logger.info(f"Successfully downloaded: {successful}")
            logger.info(f"Already existed: {skipped}")
            logger.info(f"Unrecognized program type: {unrecognized}")
            logger.info(f"Unsupported document type: {unsupported}")
            logger.info(f"Failed: {failed}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 