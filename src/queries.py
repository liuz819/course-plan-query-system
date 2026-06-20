# src/queries.py - All query implementations
from src.database import get_connection


def format_row(row):
    """Convert a sqlite3.Row to a dict for display."""
    return dict(row)


def query_required_courses(major_name):
    """查询某专业的必修课列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.short_name as school, c.code, c.name, c.credits, c.total_hours,
               c.assessment_method, mc.semester, mc.course_type, mc.weekly_hours
        FROM major_courses mc
        JOIN courses c ON mc.course_id = c.id
        JOIN majors m ON mc.major_id = m.id
        JOIN colleges col ON m.college_id = col.id
        JOIN schools s ON col.school_id = s.id
        WHERE m.name = ? AND mc.course_type LIKE '%必修%'
        ORDER BY s.short_name, mc.semester, c.code
    """, (major_name,))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


def query_course_info(course_name):
    """查询某门课程的学分、学时信息"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.code, c.name, c.credits, c.total_hours, 
               c.lecture_hours, c.practice_hours, c.assessment_method
        FROM courses c
        WHERE c.name LIKE ?
        ORDER BY c.name
    """, (f"%{course_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


def query_total_credits(major_name):
    """查询某专业的总学分要求"""
    conn = get_connection()
    cursor = conn.cursor()
    # Method 1: Get stored total_credits from majors table
    cursor.execute("""
        SELECT m.name, m.total_credits, m.duration, c.name as college_name, s.name as school_name
        FROM majors m
        JOIN colleges c ON m.college_id = c.id
        JOIN schools s ON c.school_id = s.id
        WHERE m.name = ?
    """, (major_name,))
    rows = cursor.fetchall()
    
    # Method 2: Also calculate actual total credits from courses
    cursor.execute("""
        SELECT SUM(c.credits) as actual_credits, 
               COUNT(*) as course_count,
               COUNT(DISTINCT mc.course_type) as type_count
        FROM major_courses mc
        JOIN courses c ON mc.course_id = c.id
        JOIN majors m ON mc.major_id = m.id
        WHERE m.name = ?
    """, (major_name,))
    actual = cursor.fetchone()
    conn.close()
    
    result = [format_row(r) for r in rows]
    if actual:
        result.append({"说明": "根据课程实际累计", "实际学分合计": actual["actual_credits"], "课程数量": actual["course_count"]})
    return result


def query_majors_by_course(course_name):
    """查询开设某门课程的所有专业"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT m.name as major_name, 
               col.name as college_name, 
               s.name as school_name,
               mc.course_type, mc.semester
        FROM major_courses mc
        JOIN courses c ON mc.course_id = c.id
        JOIN majors m ON mc.major_id = m.id
        JOIN colleges col ON m.college_id = col.id
        JOIN schools s ON col.school_id = s.id
        WHERE c.name LIKE ?
        ORDER BY s.name, col.name, m.name
    """, (f"%{course_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


def query_college_overview(college_name):
    """查询某学院下所有专业的培养方案概览"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.name as major_name,
               m.major_type,
               m.total_credits,
               m.education_level,
               m.duration,
               (SELECT COUNT(*) FROM major_courses mc2 WHERE mc2.major_id = m.id) as course_count,
               (SELECT SUM(c2.credits) FROM major_courses mc2 
                JOIN courses c2 ON mc2.course_id = c2.id 
                WHERE mc2.major_id = m.id) as total_credits_actual
        FROM majors m
        JOIN colleges c ON m.college_id = c.id
        WHERE c.name LIKE ?
        ORDER BY m.name
    """, (f"%{college_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


def search_courses(keyword):
    """支持关键词模糊搜索课程名称"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT c.code, c.name, c.credits, c.total_hours, 
               c.assessment_method,
               (SELECT COUNT(*) 
                FROM major_courses mc2 
                JOIN majors m ON mc2.major_id = m.id 
                WHERE mc2.course_id = c.id) as offered_by_majors
        FROM courses c
        WHERE c.name LIKE ?
        ORDER BY c.name
        LIMIT 50
    """, (f"%{keyword}%",))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


def query_cross_school_comparison(major_name):
    """跨校对比：对比相同专业在两所学校的课程设置（Module B）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
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
        ORDER BY s.name
    """, (f"%{major_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


def query_cross_school_course_diff(major_name):
    """跨校对比：对比两校同一专业的课程设置异同（Module B）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name as school_name, c.code, c.name, c.credits, 
               mc.course_type, mc.semester
        FROM majors m
        JOIN colleges col ON m.college_id = col.id
        JOIN schools s ON col.school_id = s.id
        JOIN major_courses mc ON mc.major_id = m.id
        JOIN courses c ON mc.course_id = c.id
        WHERE m.name LIKE ?
        ORDER BY s.name, c.name
    """, (f"%{major_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [format_row(r) for r in rows]


QUERY_LIST = [
    {"id": "1", "name": "必修课列表", "desc": "查询某专业的必修课列表", "fn": query_required_courses, "param": "专业名称"},
    {"id": "2", "name": "课程信息", "desc": "查询某门课程的学分、学时信息", "fn": query_course_info, "param": "课程名称（支持模糊搜索）"},
    {"id": "3", "name": "总学分要求", "desc": "查询某专业的总学分要求", "fn": query_total_credits, "param": "专业名称"},
    {"id": "4", "name": "开设课程的专业", "desc": "查询开设某门课程的所有专业", "fn": query_majors_by_course, "param": "课程名称"},
    {"id": "5", "name": "学院概览", "desc": "查询某学院下所有专业的培养方案概览", "fn": query_college_overview, "param": "学院名称"},
    {"id": "6", "name": "模糊搜索课程", "desc": "关键词模糊搜索课程名称", "fn": search_courses, "param": "关键词"},
    {"id": "7", "name": "跨校对比总览", "desc": "跨校对比相同专业的总学分等（模块B）", "fn": query_cross_school_comparison, "param": "专业名称"},
    {"id": "8", "name": "跨校课程对比", "desc": "跨校对比相同专业的课程设置差异（模块B）", "fn": query_cross_school_course_diff, "param": "专业名称"},
]
