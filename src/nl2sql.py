# src/nl2sql.py - Natural Language to SQL converter (Module B)
# Uses rule-based approach - no external LLM API needed

import re
from src.database import get_connection


def get_major_list():
    """Get list of all majors."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM majors ORDER BY name")
    majors = [row["name"] for row in cursor.fetchall()]
    conn.close()
    return majors


def get_school_list():
    """Get list of all schools."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, short_name FROM schools")
    schools = [(row["name"], row["short_name"]) for row in cursor.fetchall()]
    conn.close()
    return schools


def extract_major(text):
    """Extract major name from natural language query."""
    majors = get_major_list()
    # Sort by length (longest first) to match more specific names first
    majors_sorted = sorted(majors, key=len, reverse=True)
    for m in majors_sorted:
        if m in text:
            return m
    # Try partial matching by stripping common suffixes from the query and matching
    # e.g. "计算机专业" should match "计算机科学与技术"
    # Sort by length ASCENDING (shortest first) so "计算机科学与技术"(8) wins
    # over "计算机类（含计算机科学与技术、人工智能）"(18) when core="计算机" matches both
    stripped = text.replace("专业", "").replace("的", "").strip()
    majors_shortest_first = sorted(majors, key=len)
    for m in majors_shortest_first:
        for n in range(min(len(m), 6), 1, -1):
            core = m[:n]
            if core in stripped:
                return m
    return None


def extract_school(text):
    """Extract school name from natural language query."""
    schools = get_school_list()
    for name, short in schools:
        if name in text or short in text:
            return name
    return None


def extract_course_keyword(text):
    """Extract course keyword from natural language query."""
    # First, remove any known major names
    majors = get_major_list()
    for m in sorted(majors, key=len, reverse=True):
        text = text.replace(m, "")

    conn = get_connection()
    cursor = conn.cursor()

    # Extract potential keywords by removing query prefixes/suffixes
    cleaned = text
    prefixes = ["搜索包含", "搜索", "查询", "查找", "找", "看看", "搜一下", "关于", "包含"]
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    # Iteratively strip known suffixes (from longest to shortest to avoid partial matches)
    suffixes = ["的学分和学时", "的课程设置", "的学分", "的学时", "的信息",
                "这门课", "的课程", "有哪些", "是什么", "是多少", "含"]
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                changed = True
                break

    # Remove common particles
    for p in ["的", "和", "与", "了", "吗", "呢", "吧", "啊", "这门", "这个", "那个"]:
        cleaned = cleaned.replace(p, "")

    cleaned = cleaned.strip().strip("，").strip("。").strip()

    # Try exact match first
    if len(cleaned) >= 2:
        cursor.execute("SELECT name FROM courses WHERE name = ? LIMIT 1", (cleaned,))
        match = cursor.fetchone()
        if match:
            conn.close()
            return match["name"]

        # Try fuzzy match
        cursor.execute("SELECT name FROM courses WHERE name LIKE ? LIMIT 1", (f"%{cleaned}%",))
        match = cursor.fetchone()
        if match:
            conn.close()
            return match["name"]

        # Try matching first N characters of cleaned text (for partial names like "数据" → "数据结构")
        for n in range(len(cleaned), 1, -1):
            cursor.execute("SELECT name FROM courses WHERE name LIKE ? LIMIT 1", (f"{cleaned[:n]}%",))
            match = cursor.fetchone()
            if match:
                conn.close()
                return match["name"]

        conn.close()
        return cleaned
    conn.close()
    return None


# Query matchers: (pattern, SQL generator)
def match_required_courses(text, major_name):
    """匹配必修课查询"""
    patterns = [
        r"必修",
        r"必须修读",
        r"专业核心",
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def match_course_info(text):
    """匹配课程信息查询"""
    patterns = [
        r"学分",
        r"学时",
        r"课程信息",
        r"是多少",
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def match_total_credits(text):
    """匹配总学分查询"""
    patterns = [
        r"总学分",
        r"最低学分",
        r"毕业学分",
        r"学分要求",
        r"多少学分",
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def match_cross_school(text):
    """匹配跨校对比查询"""
    patterns = [
        r"对比",
        r"差异",
        r"不同",
        r"异同",
        r"两校",
        r"区别",
        r"跨校",
    ]
    has_pattern = any(re.search(p, text) for p in patterns)
    schools = get_school_list()
    school_count = sum(1 for name, short in schools if name in text or short in text or name[:2] in text)
    return has_pattern or school_count > 0


def match_search(text):
    """匹配模糊搜索查询"""
    patterns = [
        r"含.*的",
        r"关于",
        r"关键词",
        r"模糊",
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def interpret_nl_query(text):
    """
    Convert natural language query to SQL and execute.
    Tries LLM first (if API key configured), falls back to rule-based.
    Returns (sql, params, result_description, results)
    """
    # Try LLM first (falls back to None if no API key or error)
    from src.nl2sql_llm import interpret_with_llm
    llm_result = interpret_with_llm(text)
    if llm_result is not None:
        return llm_result

    # ── Rule-based fallback ──────────────────────────────
    conn = get_connection()
    try:
        cursor = conn.cursor()

        major_name = extract_major(text)
        course_keyword = extract_course_keyword(text)
        is_cross = match_cross_school(text)

        # Rule 1: 必修课查询
        if major_name and match_required_courses(text, major_name):
            sql = """
                SELECT c.code, c.name, c.credits, c.total_hours,
                       c.assessment_method, mc.semester, mc.course_type
                FROM major_courses mc
                JOIN courses c ON mc.course_id = c.id
                JOIN majors m ON mc.major_id = m.id
                WHERE m.name = ? AND mc.course_type LIKE '%必修%'
                ORDER BY mc.semester, c.code
            """
            cursor.execute(sql, (major_name,))
            desc = f"{major_name} 的必修课列表"
            return sql, (major_name,), desc, [dict(r) for r in cursor.fetchall()]

        # Rule 2: 总学分查询
        if major_name and match_total_credits(text):
            sql = """
                SELECT m.name, m.total_credits, m.duration,
                       (SELECT SUM(c2.credits) FROM major_courses mc2
                        JOIN courses c2 ON mc2.course_id = c2.id
                        WHERE mc2.major_id = m.id) as actual_credits
                FROM majors m
                WHERE m.name = ?
            """
            cursor.execute(sql, (major_name,))
            desc = f"{major_name} 的学分要求"
            return sql, (major_name,), desc, [dict(r) for r in cursor.fetchall()]

        # Rule 3: 跨校对比（两校同一专业对比）
        if is_cross and major_name:
            sql = """
                SELECT s.name as school_name,
                       m.name as major_name,
                       m.total_credits,
                       COUNT(DISTINCT mc.course_id) as course_count,
                       SUM(c.credits) as total_credits_actual
                FROM majors m
                JOIN colleges col ON m.college_id = col.id
                JOIN schools s ON col.school_id = s.id
                LEFT JOIN major_courses mc ON mc.major_id = m.id
                LEFT JOIN courses c ON mc.course_id = c.id
                WHERE m.name LIKE ?
                GROUP BY s.id, m.id
            """
            cursor.execute(sql, (f"%{major_name}%",))
            desc = f"「{major_name}」在两校的对比"
            return sql, (f"%{major_name}%",), desc, [dict(r) for r in cursor.fetchall()]

        # Rule 4: 课程信息查询
        if course_keyword and match_course_info(text):
            sql = """
                SELECT c.code, c.name, c.credits, c.total_hours,
                       c.lecture_hours, c.practice_hours, c.assessment_method
                FROM courses c
                WHERE c.name LIKE ?
            """
            param = f"%{course_keyword}%"
            cursor.execute(sql, (param,))
            desc = f"课程「{course_keyword}」的信息"
            return sql, (param,), desc, [dict(r) for r in cursor.fetchall()]

        # Rule 4b: 跨校对比 (if is_cross but no major extracted)
        if is_cross:
            sql = """
                SELECT s.name as school_name, m.name as major_name,
                       m.total_credits, COUNT(DISTINCT mc.course_id) as course_count
                FROM majors m
                JOIN colleges col ON m.college_id = col.id
                JOIN schools s ON col.school_id = s.id
                LEFT JOIN major_courses mc ON mc.major_id = m.id
                GROUP BY m.id
                ORDER BY s.name, m.name
            """
            cursor.execute(sql)
            desc = "所有专业的跨校对比（请指定具体专业以获得更详细对比）"
            return sql, (), desc, [dict(r) for r in cursor.fetchall()]

        # Rule 5: 模糊搜索
        search_triggers = ["搜索", "查找", "包含", "关于", "含", "找"]
        has_search = any(t in text for t in search_triggers)
        if course_keyword and (has_search or not major_name):
            sql = """
                SELECT c.code, c.name, c.credits, c.total_hours, c.assessment_method
                FROM courses c
                WHERE c.name LIKE ?
                ORDER BY c.name
                LIMIT 20
            """
            param = f"%{course_keyword}%"
            cursor.execute(sql, (param,))
            desc = f"搜索包含「{course_keyword}」的课程"
            return sql, (param,), desc, [dict(r) for r in cursor.fetchall()]

        # Fallback: search all courses for the major
        if major_name:
            sql = """
                SELECT c.code, c.name, c.credits, mc.course_type, mc.semester
                FROM major_courses mc
                JOIN courses c ON mc.course_id = c.id
                JOIN majors m ON mc.major_id = m.id
                WHERE m.name LIKE ?
                ORDER BY mc.semester, c.code
            """
            cursor.execute(sql, (f"%{major_name}%",))
            desc = f"查询「{major_name}」的全部课程"
            return sql, (f"%{major_name}%",), desc, [dict(r) for r in cursor.fetchall()]

        return None, None, "无法理解您的查询，请尝试更明确的表达", []
    finally:
        conn.close()


# Test cases for Module B
TEST_CASES = [
    {"query": "对比两校计算机科学与技术专业的课程差异", "expected": "跨校课程对比"},
    {"query": "查询计算机科学与技术的必修课", "expected": "必修课列表"},
    {"query": "计算机科学与技术专业的总学分是多少", "expected": "总学分"},
    {"query": "数据结构这门课的学分和学时", "expected": "课程信息"},
    {"query": "对比西南财经大学和上海财经大学的金融学专业", "expected": "跨校对比"},
    {"query": "搜索包含数据库的课程", "expected": "模糊搜索"},
    {"query": "查询人工智能专业有哪些课程", "expected": "全部课程"},
    {"query": "对比两校计算机专业的总学分差异", "expected": "跨校对比"},
    {"query": "两校金融学专业的课程设置有什么异同", "expected": "跨校课程对比"},
    {"query": "金融学专业需要修多少学分", "expected": "总学分"},
]


if __name__ == "__main__":
    print("=" * 60)
    print("  NL2SQL 接口测试")
    print("=" * 60)
    for tc in TEST_CASES:
        sql, params, desc, results = interpret_nl_query(tc["query"])
        print(f"\nQ: {tc['query']}")
        print(f"  => {desc}")
        print(f"  SQL: {sql[:80] if sql else 'N/A'}...")
        print(f"  结果数: {len(results)}")
