#!/usr/bin/env python3
"""
培养方案 PDF 解析器
从西南财经大学培养方案 PDF 中提取课程数据

使用方法：
  python scripts/parse_pdf.py                     # 解析并打印所有数据
  python scripts/parse_pdf.py --import-db         # 解析并导入数据库
  python scripts/parse_pdf.py --list-majors       # 仅列出所有专业
"""
import zipfile, zlib, re, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# 1. ZIP / PDF 读取工具
# ============================================================

ZIP_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "培养方案2.zip")
# Fallback to the zip we downloaded earlier
ALT_ZIP = "D:/CodexProjects/培养方案数据库系统/data/培养方案2.zip"
if not os.path.exists(ZIP_PATH):
    ZIP_PATH = ALT_ZIP


def get_pdf_list():
    """List all PDFs in the ZIP with their info."""
    z = zipfile.ZipFile(ZIP_PATH)
    names = z.namelist()
    pdfs = []
    for i, n in enumerate(names):
        if n.endswith(".pdf"):
            # Extract college name from path
            parts = n.split("/")
            college_folder = ""
            for p in parts:
                if any(c.isalpha() for c in p) and "学院" in p:
                    college_folder = p
                    break
            pdfs.append({"index": i, "path": n, "folder": college_folder})
    z.close()
    return pdfs


def read_pdf_bytes(index):
    """Read PDF bytes from ZIP by index."""
    z = zipfile.ZipFile(ZIP_PATH)
    names = z.namelist()
    data = z.read(names[index])
    z.close()
    return data


def decompress_streams(pdf_data):
    """Decompress all streams in a PDF. Returns list of (index, content) tuples."""
    text = pdf_data.decode("latin-1")
    streams = re.findall(r"stream\n(.+?)endstream", text, re.DOTALL)
    results = []
    for i, s in enumerate(streams):
        s = s.strip()
        data = s.encode("latin-1")
        decoded = None
        # Try different decompression methods
        for wbits in [15, -zlib.MAX_WBITS, 31, 0]:
            try:
                decoded = zlib.decompress(data, wbits)
                break
            except:
                continue
        if decoded:
            try:
                content = decoded.decode("utf-8", errors="replace")
            except:
                content = decoded.decode("latin-1", errors="replace")
            results.append((i, content))
    return results


# ============================================================
# 2. CMap 解析器
# ============================================================

def parse_cmap(content):
    """
    Parse a CMap stream to extract CID -> Unicode mappings.
    Returns a dict like {3: "计", 4: "算", ...}
    """
    mapping = {}
    # Match beginbfchar ... endbfchar blocks
    bfchar_blocks = re.findall(r"beginbfchar\n(.*?)endbfchar", content, re.DOTALL)
    for block in bfchar_blocks:
        for line in block.strip().split("\n"):
            line = line.strip()
            match = re.match(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", line)
            if match:
                cid = int(match.group(1), 16)
                unicode_val = int(match.group(2), 16)
                mapping[cid] = chr(unicode_val)
    
    # Also match beginbfrange ... endbfrange
    bfrange_blocks = re.findall(r"beginbfrange\n(.*?)endbfrange", content, re.DOTALL)
    for block in bfrange_blocks:
        for line in block.strip().split("\n"):
            line = line.strip()
            match = re.match(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", line)
            if match:
                start_cid = int(match.group(1), 16)
                end_cid = int(match.group(2), 16)
                start_unicode = int(match.group(3), 16)
                for offset in range(end_cid - start_cid + 1):
                    cid = start_cid + offset
                    mapping[cid] = chr(start_unicode + offset)
    
    return mapping


def build_cmap_from_pdf(pdf_data):
    """
    Extract all CMap tables from a PDF and build a unified character map.
    """
    streams = decompress_streams(pdf_data)
    charmap = {}
    for idx, content in streams:
        if "/CIDInit" in content or "/CMapName" in content:
            cmap = parse_cmap(content)
            charmap.update(cmap)
    return charmap


# ============================================================
# 3. PDF 内容解码器
# ============================================================

def decode_cid_text(content, charmap):
    """
    Decode CID text references like <000300040005> to Chinese text.
    Uses the charmap to look up each CID.
    """
    result = []
    # Match TJ arrays with hex strings
    hex_refs = re.findall(r"<([0-9A-Fa-f]+)>", content)
    for hex_str in hex_refs:
        # Split hex string into groups of 2 bytes (2 hex chars = 1 byte)
        # For Chinese chars, each CID is 2 bytes (4 hex chars)
        cids = []
        i = 0
        while i < len(hex_str):
            chunk = hex_str[i:i+4]
            if chunk:
                cids.append(int(chunk, 16))
                i += 4
            else:
                i += 2
        
        for cid in cids:
            if cid == 0:
                continue
            if cid in charmap:
                result.append(charmap[cid])
            else:
                result.append(f"[{cid:04X}]")
    
    return "".join(result)


def extract_readable_text(content, charmap):
    """
    Extract readable text from PDF content using CMap.
    """
    texts = []
    # Match TJ operator arrays
    tj_arrays = re.findall(r"\[(.*?)\]\s*TJ", content)
    for arr in tj_arrays:
        parts = re.findall(r"<([0-9A-Fa-f]+)>", arr)
        for hex_str in parts:
            cids = []
            i = 0
            while i < len(hex_str):
                chunk = hex_str[i:i+4]
                if len(chunk) == 4:
                    cids.append(int(chunk, 16))
                    i += 4
                elif len(chunk) > 0:
                    cids.append(int(chunk, 16))
                    i += len(chunk)
                else:
                    break
            
            for cid in cids:
                if cid and cid in charmap:
                    texts.append(charmap[cid])
    
    return "".join(texts)


# ============================================================
# 4. 培养方案数据提取器
# ============================================================

def extract_plan_info(pdf_data):
    """
    Extract training plan info (major name, credits, courses table) from PDF.
    """
    charmap = build_cmap_from_pdf(pdf_data)
    streams = decompress_streams(pdf_data)
    
    # Collect all text from all streams
    all_text = ""
    for idx, content in streams:
        decoded = decode_cid_text(content, charmap)
        readable = extract_readable_text(content, charmap)
        if decoded and len(decoded) > 5:
            all_text += decoded + "\n"
        if readable and len(readable) > 5:
            all_text += readable + "\n"
    
    # Extract basic info
    info = {
        "major_name": "",
        "college_name": "",
        "total_credits": 0,
        "courses": []
    }
    
    # Try to find major name
    # Look for patterns like "XXX专业人才培养方案"
    match = re.search(r"(.{2,8}专业.{0,2}人才培养方案)", all_text)
    if match:
        info["major_name"] = match.group(1)
    
    # Try to find total credits
    credit_matches = re.findall(r"(\d+)[\.\s]*学分", all_text)
    if credit_matches:
        info["total_credits"] = int(credit_matches[0])
    
    # Try to find course entries - look for rows with course codes and numbers
    # Course pattern: code (6-10 chars), name (Chinese), credits (number), hours (number)
    course_patterns = re.findall(
        r"([A-Z]{2,4}\d{3,6})"  # Course code like CS101
        r".{0,20}"               # Separator
        r"([\u4e00-\u9fff]{2,20})"  # Course name (Chinese)
        r".{0,10}"
        r"(\d+[\.\d]*)"          # Credits
        r".{0,10}"
        r"(\d+[\.\d]*)",         # Hours
        all_text
    )
    
    for m in course_patterns:
        info["courses"].append({
            "code": m[0],
            "name": m[1],
            "credits": float(m[2]),
            "hours": float(m[3])
        })
    
    return info, all_text


# ============================================================
# 5. 主逻辑
# ============================================================

def list_majors():
    """List all majors available in the ZIP."""
    pdfs = get_pdf_list()
    print(f"共找到 {len(pdfs)} 个专业培养方案 PDF：")
    for p in pdfs:
        # Extract readable info from filename
        parts = p["path"].split("/")
        filename = parts[-1].replace(".pdf", "")
        folder = p["folder"] or "?"
        print(f"  [{p['index']}] {folder}/  {filename}")


def parse_all(max_pdfs=5):
    """Parse multiple PDFs and aggregate data."""
    pdfs = get_pdf_list()
    results = []
    
    for p in pdfs[:max_pdfs]:
        print(f"\n解析: [{p['index']}] {p['folder']}...")
        try:
            data = read_pdf_bytes(p["index"])
            info, all_text = extract_plan_info(data)
            info["source"] = p["path"]
            results.append(info)
            
            # Print summary
            print(f"  专业: {info['major_name'][:30]}")
            print(f"  学分: {info['total_credits']}")
            print(f"  课程数: {len(info['courses'])}")
            if info['courses']:
                print(f"  示例课程: {info['courses'][0]['name']} ({info['courses'][0]['credits']}学分)")
            
            # Print raw text preview
            print(f"  原始文本预览: {all_text[:200]}")
        except Exception as e:
            print(f"  解析失败: {e}")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="培养方案PDF解析器")
    parser.add_argument("--list-majors", action="store_true", help="列出所有专业")
    parser.add_argument("--index", type=int, default=None, help="指定PDF索引")
    parser.add_argument("--import-db", action="store_true", help="将解析结果导入数据库")
    args = parser.parse_args()
    
    if args.list_majors:
        list_majors()
    elif args.index is not None:
        data = read_pdf_bytes(args.index)
        info, text = extract_plan_info(data)
        print(f"=== 专业: {info['major_name']} ===")
        print(f"总学分: {info['total_credits']}")
        print(f"课程数量: {len(info['courses'])}")
        print("\n=== 原始文本 ===")
        print(text[:2000])
    elif args.import_db:
        print("导入数据库功能正在开发中...")
        # This would parse all PDFs and insert into the database
    else:
        parse_all(5)
