#!/usr/bin/env python3
"""
Import real course data from SWUFE training plan PDFs (培养方案2.zip).
Replaces the hardcoded seeder.py with actual extracted data.
"""
import zipfile, io, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pdfplumber
from src.database import init_database, get_connection

ZIP_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "培养方案2.zip")


def parse_college_code(folder_name):
    match = re.match(r"(\d+)(.+)", folder_name)
    if match:
        return int(match.group(1)), match.group(2)
    return None, folder_name


def is_course_row(row):
    if not row or all(c is None or str(c).strip() == "" for c in row):
        return False
    first = str(row[0]).strip() if row[0] else ""
    return bool(re.match(r"^[A-Z]{2,4}\d{3,6}", first))


def extract_courses_from_pdf(pdf_data):
    courses = []
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                for row in table:
                    if not row:
                        continue
                    first_cell = str(row[0]).strip() if row[0] else ""

                    # Skip header / non-course rows
                    skip_keywords = [
                        "课程设置", "模块及类别", "实践教学", "培养目标", "课程", "Code",
                        "综合素质", "数学类课程", "计算机类课程", "合计", "小计"
                    ]
                    if not first_cell or any(kw in first_cell for kw in skip_keywords):
                        continue
                    if "课程代码" in first_cell or "Course" in first_cell:
                        continue
                    if not is_course_row(row):
                        continue

                    code = first_cell.replace("\n", "").strip()

                    # Classify cells: numeric, course_type, name, semester
                    name = ""
                    credits = None
                    total_hours = None
                    lecture_hours = None
                    practice_hours = None
                    course_type = "必修"
                    semester = None

                    numeric_vals = []
                    for cell in row[1:]:
                        val = str(cell).strip() if cell else ""
                        if not val:
                            continue
                        first_line = val.split("\n")[0].strip()
                        num_match = re.match(r"^([\d.]+)$", first_line)
                        if num_match:
                            numeric_vals.append(float(num_match.group(1)))

                    # Parse course type from any cell
                    for cell in row:
                        val = str(cell).strip() if cell else ""
                        if "限选" in val:
                            course_type = "限选"
                        elif "选修" in val and "必修" not in val:
                            course_type = "选修"

                    # Find course name: first Chinese text cell that's not a college/department
                    for cell in row[1:]:
                        val = str(cell).strip() if cell else ""
                        if not val:
                            continue
                        first_line = val.split("\n")[0].strip()
                        has_chinese = any('一' <= c <= '鿿' for c in first_line)
                        is_number = re.match(r"^[\d.]+$", first_line)
                        if has_chinese and not is_number:
                            if "学院" not in first_line and len(first_line) >= 2:
                                name = first_line
                                break

                    # Parse numeric columns
                    if numeric_vals:
                        credits = numeric_vals[0]
                        if len(numeric_vals) >= 2:
                            total_hours = numeric_vals[1]
                        if len(numeric_vals) >= 3:
                            lecture_hours = numeric_vals[2]
                        if len(numeric_vals) >= 4:
                            practice_hours = numeric_vals[3]

                    # Try to find semester from last column
                    for cell in reversed(row):
                        val = str(cell).strip() if cell else ""
                        if val and re.match(r"^\d$", val):
                            sem = int(val)
                            if 1 <= sem <= 8:
                                semester = sem
                                break

                    # Deduce total_hours from credits if missing
                    if total_hours is None and credits:
                        total_hours = round(credits * 17)

                    if name and credits:
                        courses.append({
                            "code": code,
                            "name": name,
                            "credits": credits,
                            "total_hours": total_hours,
                            "lecture_hours": lecture_hours,
                            "practice_hours": practice_hours,
                            "course_type": course_type,
                            "semester": semester,
                        })
    return courses


def import_all():
    if not os.path.exists(ZIP_PATH):
        print(f"[ERROR] ZIP not found: {ZIP_PATH}")
        return

    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO schools (id, name, short_name) VALUES (1, '西南财经大学', 'SWUFE')")
    cursor.execute("INSERT OR IGNORE INTO schools (id, name, short_name) VALUES (2, '上海财经大学', 'SUFE')")

    z = zipfile.ZipFile(ZIP_PATH)

    # Get PDF infos (ZIP stores filenames in GBK, decode properly)
    pdf_infos = []
    for info in z.infolist():
        raw_name = info.filename.encode("cp437")
        try:
            name = raw_name.decode("gbk")
        except:
            continue
        if name.endswith(".pdf"):
            pdf_infos.append((name, info))

    total_assoc = 0
    total_courses = set()

    for pdf_path, info in pdf_infos:
        parts = pdf_path.split("/")
        folder = parts[-2] if len(parts) > 1 else ""
        filename = parts[-1].replace(".pdf", "")

        college_code, college_name = parse_college_code(folder)
        if not college_code:
            continue

        # Insert college
        cursor.execute("SELECT id FROM colleges WHERE school_id=1 AND code=?", (str(college_code),))
        row = cursor.fetchone()
        if row:
            college_id = row["id"]
        else:
            cursor.execute("INSERT INTO colleges (school_id, name, code) VALUES (1, ?, ?)",
                           (college_name, str(college_code)))
            college_id = cursor.lastrowid

        # Extract major name
        major_name = filename
        # Remove leading numbers, year prefixes, and parenthetical suffixes
        major_name = re.sub(r"^[\d]+", "", major_name)
        major_name = re.sub(r"\(.*$", "", major_name)
        major_name = re.sub(r"（.*$", "", major_name)
        major_name = major_name.strip()
        if not major_name or len(major_name) < 2:
            continue
        # Skip non-major documents
        if "教学计划" in major_name or "原则性意见" in major_name or "辅修" in major_name:
            continue

        # Insert major
        cursor.execute("INSERT OR IGNORE INTO majors (college_id, name, total_credits) VALUES (?, ?, NULL)",
                       (college_id, major_name))
        cursor.execute("SELECT id FROM majors WHERE college_id=? AND name=?", (college_id, major_name))
        major_row = cursor.fetchone()
        if not major_row:
            continue
        major_id = major_row["id"]

        # Extract courses
        try:
            pdf_data = z.read(info)
            courses = extract_courses_from_pdf(pdf_data)
        except Exception as e:
            print(f"  [SKIP] {college_name}/{major_name}: {e}")
            continue

        for c in courses:
            cursor.execute(
                """INSERT OR IGNORE INTO courses
                   (code, name, credits, total_hours, lecture_hours, practice_hours)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (c["code"], c["name"], c["credits"],
                 c.get("total_hours"), c.get("lecture_hours"), c.get("practice_hours"))
            )
            cursor.execute("SELECT id FROM courses WHERE code=?", (c["code"],))
            cr = cursor.fetchone()
            if cr:
                cursor.execute(
                    """INSERT OR IGNORE INTO major_courses
                       (major_id, course_id, course_type, semester)
                       VALUES (?, ?, ?, ?)""",
                    (major_id, cr["id"], c.get("course_type", "必修"), c.get("semester"))
                )
                total_assoc += 1
                total_courses.add(c["code"])

        if courses:
            print(f"  [{college_code}]{college_name}/{major_name}: {len(courses)} courses")

    conn.commit()
    conn.close()
    z.close()
    print(f"\n[DONE] {len(total_courses)} unique courses, {total_assoc} associations from real PDFs")


if __name__ == "__main__":
    import_all()
