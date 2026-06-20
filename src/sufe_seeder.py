#!/usr/bin/env python3
"""
Seed SUFE (上海财经大学) data using REAL course data extracted via OCR from sufe_plan.pdf.
Source: https://gongkai.sufe.edu.cn/27/a5/c12262a206757/page.htm

Data extraction: scripts/parse_sufe_ocr.py  (OCR 415 pages → structured courses)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import get_connection

# Path to OCR-extracted course data
SEEDER_DATA = os.path.join(os.path.dirname(__file__), '..', 'data', '_sufe_seeder_data.json')

# ── SUFE Colleges (verified from OCR + official website) ─────────
SUFE_COLLEGES = [
    (1, '经济学院'),
    (2, '公共经济与管理学院'),
    (3, '金融学院'),
    (4, '会计学院'),
    (5, '统计与数据科学学院'),
    (6, '信息管理与工程学院'),
    (7, '商学院'),
    (8, '法学院'),
    (9, '数学学院'),
    (10, '外国语学院'),
]

# ── SUFE Majors (verified from OCR text) ─────────────────────────
SUFE_MAJORS = [
    # (college_idx, name, total_credits)
    ('经济学院', '经济学', 151),
    ('经济学院', '经济学（基地班）', 151),
    ('经济学院', '经济学（数理经济）', 151),
    ('公共经济与管理学院', '财政学', 148),
    ('公共经济与管理学院', '税收学', 148),
    ('公共经济与管理学院', '投资学', 151),
    ('公共经济与管理学院', '行政管理', 148),
    ('公共经济与管理学院', '劳动与社会保障', 148),
    ('金融学院', '金融学', 158),
    ('金融学院', '保险学', 176),
    ('金融学院', '金融工程', 158),
    ('会计学院', '会计学', 155),
    ('会计学院', '财务管理', 155),
    ('会计学院', '会计学（ACCA方向）', 155),
    ('统计与数据科学学院', '统计学', 156),
    ('统计与数据科学学院', '经济统计学', 156),
    ('统计与数据科学学院', '数据科学与大数据技术（理科）', 156),
    ('信息管理与工程学院', '计算机科学与技术', 158),
    ('信息管理与工程学院', '信息管理与信息系统', 158),
    ('信息管理与工程学院', '数据科学与大数据技术（工科）', 158),
    ('信息管理与工程学院', '电子商务', 158),
    ('商学院', '工商管理', 153),
    ('商学院', '市场营销', 153),
    ('商学院', '国际经济与贸易', 153),
    ('商学院', '人力资源管理', 153),
    ('法学院', '法学', 155),
    ('数学学院', '数学与应用数学', 155),
    ('数学学院', '信息与计算科学', 155),
    ('外国语学院', '英语', 155),
    ('外国语学院', '商务英语', 155),
    ('外国语学院', '日语', 155),
]


def load_real_courses():
    """Load all unique courses from OCR data, deduplicated by code."""
    if not os.path.exists(SEEDER_DATA):
        print(f'[WARNING] OCR data not found at {SEEDER_DATA}')
        print('  Run: python scripts/parse_sufe_ocr.py')
        return {}

    with open(SEEDER_DATA, 'r', encoding='utf-8') as f:
        assignments = json.load(f)

    # Deduplicate by course code, keep first occurrence
    unique = {}
    for a in assignments:
        for c in a['courses']:
            code = c.get('code', '')
            if code and code not in unique:
                unique[code] = {
                    'code': code,
                    'name': c.get('name', ''),
                    'credits': c.get('credits'),
                    'course_type': c.get('course_type', '必修'),
                }

    return unique


def seed_sufe_data():
    """Import real SUFE course data into the database."""
    # Check OCR data availability FIRST (before any DB writes)
    real_courses = load_real_courses()
    if not real_courses:
        print('[SUFE] OCR data not found, skipping SUFE import entirely')
        print('  Run: python scripts/parse_sufe_ocr.py')
        return

    conn = get_connection()
    c = conn.cursor()

    # Ensure SUFE school exists
    c.execute("INSERT OR IGNORE INTO schools (id, name, short_name) VALUES (2, '上海财经大学', 'SUFE')")

    # ── Colleges ──
    college_ids = {}
    for col_code, col_name in SUFE_COLLEGES:
        c.execute("INSERT OR IGNORE INTO colleges (school_id, name, code) VALUES (2, ?, ?)",
                  (col_name, f'S{col_code:02d}'))
        c.execute("SELECT id FROM colleges WHERE school_id=2 AND name=?", (col_name,))
        row = c.fetchone()
        if row:
            college_ids[col_name] = row['id']

    # ── Majors ──
    major_ids = {}
    for college_name, major_name, credits in SUFE_MAJORS:
        col_id = college_ids.get(college_name)
        if not col_id:
            continue
        c.execute("""INSERT OR IGNORE INTO majors (college_id, name, total_credits, education_level, duration)
                     VALUES (?, ?, ?, '本科', '4年')""",
                  (col_id, major_name, credits))
        c.execute("SELECT id FROM majors WHERE college_id=? AND name=?", (col_id, major_name))
        row = c.fetchone()
        if row:
            major_ids[major_name] = row['id']

    print(f'[SUFE] Inserted {len(college_ids)} colleges, {len(major_ids)} majors')

    # ── Courses (real data from OCR) ──
    real_courses = load_real_courses()
    if not real_courses:
        conn.close()
        return

    inserted_courses = 0
    for code, info in real_courses.items():
        try:
            c.execute("""INSERT OR IGNORE INTO courses (code, name, credits)
                         VALUES (?, ?, ?)""",
                      (code, info['name'], info['credits']))
            if c.rowcount > 0:
                inserted_courses += 1
        except Exception:
            pass

    print(f'[SUFE] Inserted {inserted_courses} new courses (from {len(real_courses)} OCR-extracted)')

    # ── Major-Course Associations ──
    # Strategy: assign by college page range (OCR major names are noisy,
    # but college assignments are reliable). Each major gets all courses
    # found in its college's section of the PDF.
    with open(SEEDER_DATA, 'r', encoding='utf-8') as f:
        assignments = json.load(f)

    # Map course code → id
    c.execute("SELECT id, code FROM courses")
    code_to_id = {row['code']: row['id'] for row in c.fetchall()}

    # Collect all unique courses per college from OCR assignments
    college_courses = {}  # college_name → list of unique courses
    for a in assignments:
        col = a['college']
        if col not in college_courses:
            college_courses[col] = {}
        for course in a['courses']:
            code = course.get('code', '')
            if code and code not in college_courses[col]:
                college_courses[col][code] = course

    total_assoc = 0
    for col_name, sufe_major, _ in SUFE_MAJORS:
        mid = major_ids.get(sufe_major)
        if not mid:
            continue

        # Get courses for this major's college (try exact match, then fuzzy)
        courses = college_courses.get(col_name)
        if not courses:
            # Fuzzy match: find a college whose name is contained in col_name or vice versa
            for ocr_col, ocr_courses in college_courses.items():
                if col_name in ocr_col or ocr_col in col_name:
                    courses = ocr_courses
                    break
        if not courses:
            continue

        for code, course in courses.items():
            cid = code_to_id.get(code)
            if not cid:
                continue

            c.execute("""INSERT OR IGNORE INTO major_courses
                         (major_id, course_id, course_type, semester)
                         VALUES (?, ?, ?, ?)""",
                      (mid, cid, course.get('course_type', '必修'), None))
            if c.rowcount > 0:
                total_assoc += 1

    print(f'[SUFE] Created {total_assoc} major-course associations')

    conn.commit()
    conn.close()

    # ── Stats ──
    conn2 = get_connection()
    c2 = conn2.cursor()
    c2.execute("""SELECT m.name, COUNT(mc.id) as cnt FROM majors m
                  JOIN colleges col ON m.college_id = col.id
                  JOIN schools s ON col.school_id = s.id
                  LEFT JOIN major_courses mc ON mc.major_id = m.id
                  WHERE s.short_name = 'SUFE'
                  GROUP BY m.id ORDER BY cnt DESC""")
    print("\n[SUFE] Major course counts:")
    for r in c2.fetchall():
        print(f"  {r['name']}: {r['cnt']} courses")
    conn2.close()


if __name__ == "__main__":
    seed_sufe_data()
