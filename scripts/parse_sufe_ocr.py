#!/usr/bin/env python3
"""
Parse OCR output from SUFE training plan PDF.
Extracts: colleges, majors, courses, and major-course associations.
"""
import json, re, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

OCR_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', '_sufe_ocr_full.json')

# Known SUFE colleges (from the PDF structure, manually verified via OCR samples)
SUFE_COLLEGES = {
    '经济学院': '经济学院',
    '公共经济与管理学院': '公共经济与管理学院',
    '金融学院': '金融学院',
    '会计学院': '会计学院',
    '统计与数据科学学院': '统计与数据科学学院',
    '信息管理与工程学院': '信息管理与工程学院',
    '商学院': '商学院',
    '法学院': '法学院',
    '数学学院': '数学学院',
    '外国语学院': '外国语学院',
    '人文学院': '人文学院',
    '国际文化交流学院': '国际文化交流学院',
    '财经研究所': '财经研究所',
}


def load_ocr():
    with open(OCR_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize(text):
    """Normalize OCR text: fix common OCR errors."""
    # Remove OCR artifacts
    text = text.replace(' ', '').replace('　', '')
    return text.strip()


def extract_majors_from_pages(pages):
    """
    Find major names by looking for 'XX专业' patterns near 'XX学院'.
    Returns list of (college_name, major_name, page_num).
    """
    results = []

    for pg_str in sorted(pages.keys(), key=int):
        pg = int(pg_str)
        text = pages[pg_str]
        text_norm = normalize(text)

        # Find college
        college = None
        for cname in SUFE_COLLEGES:
            if cname in text_norm:
                college = cname
                break
        if not college:
            # Try fuzzy match for OCR errors
            for cname in SUFE_COLLEGES:
                # Check first 2 and last 2 chars
                if len(cname) >= 4:
                    if cname[:2] in text_norm and cname[-2:] in text_norm:
                        college = cname
                        break

        if not college:
            continue

        # Find major names on same or adjacent pages
        # Pattern: XX专业 or XX专业（XX方向） or XX专业(XX)
        major_pattern = r'([^\s,.，。、；;：:（）\(\)\d]{2,8}专业(?:（[^）]*）|\([^)]*\))?)'
        majors = re.findall(major_pattern, text_norm)

        for m in majors:
            m = normalize(m)
            if len(m) >= 3 and m not in ['本专业', '该专业', '各专业']:
                # Clean up common OCR noise
                m = re.sub(r'^[.。，,]+', '', m)
                m = re.sub(r'[.。，,]+$', '', m)
                if len(m) >= 3:
                    results.append((college, m, pg))

    # Deduplicate
    seen = set()
    deduped = []
    for c, m, pg in results:
        key = (c, m)
        if key not in seen:
            seen.add(key)
            deduped.append((c, m, pg))

    return deduped


def extract_course_tables(pages):
    """
    Extract courses from table pages.
    Pattern: 6-digit course code followed by course name and numbers.

    Returns dict mapping page_num -> list of (code, name, credits, course_type)
    """
    all_courses = {}  # page -> courses

    for pg_str in sorted(pages.keys(), key=int):
        pg = int(pg_str)
        text = pages[pg_str]

        # Check if this page has course codes
        codes = re.findall(r'\b(\d{6})\b', text)
        if len(codes) < 3:
            continue

        lines = text.split('\n')
        courses = []
        current_type = '必修'  # default

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Track course type from section headers
            if '必修' in line and '选修' not in line and len(line) <= 6:
                current_type = '必修'
            elif '选修' in line and '必修' not in line and len(line) <= 6:
                current_type = '选修'
            elif '通识' in line:
                current_type = '通识必修' if '必修' in line else '通识选修'
            elif '学科共同' in line or '学科基础' in line:
                current_type = '学科基础必修'
            elif '个性化' in line:
                current_type = '个性化选修'

            # Match: 6-digit code on its own or at start of line
            code_match = re.match(r'^(\d{6})$', line)
            if code_match:
                code = code_match.group(1)
                # Next non-empty line should be course name
                name = ''
                credits = None

                # Look ahead for course name and credits
                j = i + 1
                while j < len(lines) and j < i + 5:
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue

                    # If next line is another 6-digit code, skip
                    if re.match(r'^\d{6}$', next_line):
                        break

                    # If next line is mostly Chinese, it's likely the course name
                    chinese_chars = len(re.findall(r'[一-鿿]', next_line))
                    if chinese_chars >= 2 and not re.match(r'^\d', next_line):
                        if not name:
                            name = next_line
                        elif chinese_chars > len(re.findall(r'[一-鿿]', name)):
                            name = next_line
                        j += 1
                        continue

                    # Check for credit number (1-9, not 6 digits)
                    num_match = re.match(r'^(\d{1,2}(?:\.\d)?)$', next_line)
                    if num_match and not re.match(r'^\d{6}$', next_line):
                        val = float(num_match.group(1))
                        if 0.5 <= val <= 20:  # reasonable credit range
                            if credits is None:
                                credits = val
                        j += 1
                        continue

                    j += 1

                if name and credits:
                    courses.append({
                        'code': code,
                        'name': normalize(name),
                        'credits': credits,
                        'course_type': current_type,
                    })

                i = j
                continue

            i += 1

        if courses:
            all_courses[pg] = courses

    return all_courses


def assign_courses_to_majors(major_list, course_tables, pages):
    """
    Assign course table pages to the nearest preceding major.
    Strategy: each major has its courses on pages immediately following its declaration.
    """
    # Sort majors by page
    majors_sorted = sorted(major_list, key=lambda x: x[2])

    # For each major, find the course table pages that come after it
    # but before the next major
    assignments = []

    for idx, (college, major, pg) in enumerate(majors_sorted):
        start_pg = pg
        # End page is the next major's page (or end of document)
        if idx + 1 < len(majors_sorted):
            end_pg = majors_sorted[idx + 1][2]
        else:
            end_pg = 9999

        # Find course tables between start_pg and end_pg
        major_courses = []
        for course_pg in sorted(course_tables.keys()):
            if start_pg <= course_pg < end_pg:
                major_courses.extend(course_tables[course_pg])

        if major_courses:
            assignments.append({
                'college': college,
                'major': major,
                'courses': major_courses,
                'page': pg,
            })

    return assignments


def main():
    print('Loading OCR data...')
    pages = load_ocr()
    print(f'  {len(pages)} pages')

    print('\nExtracting majors...')
    majors = extract_majors_from_pages(pages)
    print(f'  Found {len(majors)} major references')
    for c, m, pg in majors:
        print(f'    p.{pg}: [{c}] {m}')

    print('\nExtracting course tables...')
    course_tables = extract_course_tables(pages)
    total_courses = sum(len(v) for v in course_tables.values())
    unique_codes = set()
    for courses in course_tables.values():
        for c in courses:
            unique_codes.add(c['code'])
    print(f'  Found {total_courses} course entries on {len(course_tables)} pages')
    print(f'  Unique course codes: {len(unique_codes)}')

    print('\nAssigning courses to majors...')
    assignments = assign_courses_to_majors(majors, course_tables, pages)

    # Save structured data
    output = {
        'majors': [(c, m, pg) for c, m, pg in majors],
        'course_tables': {str(k): v for k, v in course_tables.items()},
        'assignments': [{**a, 'courses_count': len(a['courses'])} for a in assignments],
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', '_sufe_parsed.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'\nSaved to {output_path}')

    # Print summary
    print('\n' + '=' * 60)
    print('SUFE Data Extraction Summary')
    print('=' * 60)
    for a in assignments:
        print(f'\n[{a["college"]}] {a["major"]}')
        print(f'  Courses: {len(a["courses"])}')
        # Show first 3 courses
        for c in a['courses'][:3]:
            print(f'    {c["code"]} {c["name"]} ({c["credits"]}学分) [{c["course_type"]}]')
        if len(a['courses']) > 3:
            print(f'    ... and {len(a["courses"]) - 3} more')

    # Save detailed assignments for seeder
    seeder_path = os.path.join(os.path.dirname(__file__), '..', 'data', '_sufe_seeder_data.json')
    with open(seeder_path, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, ensure_ascii=False, indent=2)
    print(f'\nSeeder data saved to {seeder_path}')


if __name__ == '__main__':
    main()
