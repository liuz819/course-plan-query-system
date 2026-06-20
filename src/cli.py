# -*- coding: utf-8 -*-
"""CLI interface for the training plan database system."""
import sys
from src.queries import QUERY_LIST
from src.nl2sql import interpret_nl_query


def _char_width(ch):
    """Return display width of a single character. CJK chars = 2, ASCII = 1."""
    code = ord(ch)
    if (0x1100 <= code <= 0x115F or    # Hangul Jamo
        0x2E80 <= code <= 0xA4CF or    # CJK Radicals Supplement .. Yi
        0xA960 <= code <= 0xA97C or    # Hangul Jamo Extended-A
        0xAC00 <= code <= 0xD7A3 or    # Hangul Syllables
        0xF900 <= code <= 0xFAFF or    # CJK Compatibility Ideographs
        0xFE30 <= code <= 0xFE6F or    # CJK Compatibility Forms
        0xFF01 <= code <= 0xFF60 or    # Fullwidth Forms
        0xFFE0 <= code <= 0xFFE6 or
        0x1F000 <= code <= 0x1F9FF or  # Emoticons
        0x20000 <= code <= 0x2FA1F):   # CJK Unified Ideographs Extension B+
        return 2
    return 1


def _display_width(s):
    """Calculate terminal display width of a string (CJK chars count as 2)."""
    return sum(_char_width(ch) for ch in str(s))


def _ljust_cjk(s, width):
    """Left-justify string accounting for CJK display width."""
    s = str(s)
    dw = _display_width(s)
    if dw >= width:
        return s
    return s + " " * (width - dw)


def print_table(rows, max_col_width=40):
    """Pretty print query results as a table."""
    if not rows:
        print("  (无结果)")
        return
    headers = list(rows[0].keys())
    col_widths = {}
    for h in headers:
        max_len = _display_width(h)
        for row in rows:
            val = str(row.get(h, ""))
            dw = _display_width(val)
            max_len = max(min(dw, max_col_width), max_len)
        col_widths[h] = max_len

    sep = "+" + "+".join("-" * (col_widths[h] + 2) for h in headers) + "+"
    print(sep)
    header_line = "|" + "".join(f" {_ljust_cjk(h, col_widths[h])} |" for h in headers)
    print(header_line)
    print(sep)
    for row in rows:
        cells = []
        for h in headers:
            val = str(row.get(h, ""))
            # Truncate with display-width awareness
            truncated = ""
            tw = 0
            for ch in val:
                cw = _char_width(ch)
                if tw + cw > max_col_width:
                    truncated += "..."
                    break
                truncated += ch
                tw += cw
            if _display_width(val) <= max_col_width:
                truncated = val
            cells.append(f" {_ljust_cjk(truncated, col_widths[h])} |")
        print("|" + "".join(cells))
    print(sep)
    print(f"  共 {len(rows)} 条记录")


def interactive_mode():
    """Interactive CLI mode."""
    print("=" * 60)
    print("  培养方案数据库查询系统")
    print("  支持西南财经大学 + 上海财经大学跨校对比")
    print("=" * 60)
    
    while True:
        print()
        print("-" * 60)
        print("  请选择查询类型：")
        print("-" * 60)
        for q in QUERY_LIST:
            print(f"  [{q['id']}] {q['name']} - {q['desc']}")
        print("  [9] 自然语言查询(NL2SQL) - 用中文自然语言提问，自动转SQL")
        print("  [0] 退出系统")
        
        choice = input("请输入编号: ").strip()
        if choice == "0":
            print("感谢使用！")
            break
        
        if choice == "9":
            param = input("请输入自然语言查询: ").strip()
            if not param:
                print("输入不能为空")
                continue
            try:
                sql, params, desc, results = interpret_nl_query(param)
                print(f"\n--- NL2SQL: {desc} ---")
                if results:
                    print_table(results)
                else:
                    print("  (无结果)")
            except Exception as e:
                print(f"NL2SQL查询出错: {e}")
            continue
        
        selected = None
        for q in QUERY_LIST:
            if q['id'] == choice:
                selected = q
                break
        
        if not selected:
            print("无效选择，请重新输入")
            continue
        
        param = input(f"请输入{selected['param']}: ").strip()
        if not param:
            print("输入不能为空")
            continue
        
        print(f"\n--- {selected['name']}: {param} ---")
        try:
            results = selected['fn'](param)
            print_table(results)
        except Exception as e:
            print(f"查询出错: {e}")


def quick_query(query_id, param):
    """Run a single query and print results."""
    if query_id == '9':
        try:
            sql, params, desc, results = interpret_nl_query(param)
            print(f"\n--- NL2SQL: {desc} ---")
            if results:
                print_table(results)
            else:
                print("  (无结果)")
            return
        except Exception as e:
            print(f"NL2SQL查询出错: {e}")
            return
    
    for q in QUERY_LIST:
        if q['id'] == query_id:
            try:
                results = q['fn'](param)
                print(f"\n--- {q['name']}: {param} ---")
                print_table(results)
                return
            except Exception as e:
                print(f"查询出错: {e}")
                return
    print(f"未找到查询编号: {query_id}")


def show_help():
    print("用法:")
    print("  python run.py              # 进入交互模式")
    print("  python run.py <编号> <参数>  # 直接执行查询")
    print()
    print("查询编号:")
    for q in QUERY_LIST:
        print(f"  {q['id']}: {q['name']}")
    print("  9: 自然语言查询(NL2SQL)")
    print()
    print("示例:")
    print("  python run.py 1 计算机科学与技术")
    print("  python run.py 6 数据结构")
    print("  python run.py 7 金融学")
    print("  python run.py 9 对比两校计算机专业的课程差异")


def main():
    if len(sys.argv) == 1:
        interactive_mode()
    elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
        show_help()
    elif len(sys.argv) >= 3:
        quick_query(sys.argv[1], sys.argv[2])
    else:
        show_help()


if __name__ == "__main__":
    main()
