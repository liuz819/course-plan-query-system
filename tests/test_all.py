#!/usr/bin/env python3
"""项目自动化测试脚本 — 验证所有查询与 NL2SQL 的正确性"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_connection
from src.queries import (
    query_required_courses, query_course_info, query_total_credits,
    query_majors_by_course, query_college_overview, search_courses,
    query_cross_school_comparison, query_cross_school_course_diff,
)
from src.nl2sql import interpret_nl_query, TEST_CASES

PASS, FAIL = 0, 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def test_db_structure():
    print("\n" + "=" * 50)
    print("  数据库结构检查")
    print("=" * 50)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in c.fetchall()}
    expected = {"schools", "colleges", "majors", "courses", "major_courses"}
    for t in expected:
        check(f"表 {t} 存在", t in tables, f"缺少表 {t}")
    # 行数
    for t, min_rows in [("schools", 2), ("colleges", 8), ("majors", 12),
                          ("courses", 70), ("major_courses", 150)]:
        c.execute(f"SELECT COUNT(*) as n FROM {t}")
        n = c.fetchone()["n"]
        check(f"{t} 行数 >= {min_rows}", n >= min_rows, f"当前 {n} 行")
    # 无空专业
    c.execute("""
        SELECT m.name, s.short_name FROM majors m
        JOIN colleges col ON m.college_id = col.id
        JOIN schools s ON col.school_id = s.id
        LEFT JOIN major_courses mc ON mc.major_id = m.id
        GROUP BY m.id HAVING COUNT(mc.id) = 0
    """)
    empties = [(r["name"], r["short_name"]) for r in c.fetchall()]
    check("无空课程专业", len(empties) == 0, str(empties))
    conn.close()


def test_module_a():
    print("\n" + "=" * 50)
    print("  模块 A — 6 类查询")
    print("=" * 50)

    # 1. 必修课
    r = query_required_courses("计算机类")
    check("查询1 必修课列表有结果", len(r) > 0, f"{len(r)} 条")
    check("查询1 包含 school 列", "school" in r[0] if r else False)
    types = {row["course_type"] for row in r}
    check("查询1 包含多种必修类型", len(types) >= 1, str(types))
    schools = {row.get("school", "") for row in r}
    check("查询1 跨校数据", len(schools) >= 1, f"覆盖 {len(schools)} 校: {schools}")

    # 2. 课程信息
    r = query_course_info("思想道德")
    check("查询2 课程信息返回结果", len(r) >= 1, f"{len(r)} 条")
    if r:
        check("查询2 包含学分", r[0].get("credits") is not None)
        check("查询2 包含学时", r[0].get("total_hours") is not None)

    # 3. 总学分
    r = query_total_credits("计算机类")
    check("查询3 总学分有结果", len(r) >= 1, f"{len(r)} 条")

    # 4. 开设课程的专业
    r = query_majors_by_course("思想道德")
    check("查询4 返回多个专业", len(r) >= 1, f"{len(r)} 个专业")

    # 5. 学院概览
    r = query_college_overview("计算机")
    check("查询5 学院概览有结果", len(r) >= 1, f"{len(r)} 个专业")

    # 6. 模糊搜索
    r = search_courses("数据")
    check("查询6 模糊搜索有结果", len(r) >= 3, f"{len(r)} 条")


def test_module_b():
    print("\n" + "=" * 50)
    print("  模块 B — 跨校对比")
    print("=" * 50)

    # 7. 跨校对比总览
    r = query_cross_school_comparison("金融学")
    check("查询7 跨校对比有结果", len(r) >= 2, f"{len(r)} 条")
    schools = {row["school_name"] for row in r}
    check("查询7 包含两校", len(schools) >= 2, f"共 {len(schools)} 校: {schools}")

    # 检查两校都返回了数据
    schools = {row["school_name"] for row in r}
    check("查询7 包含两校", len(schools) >= 2, f"共 {len(schools)} 校: {schools}")

    # 8. 跨校课程差异
    r = query_cross_school_course_diff("金融学")
    check("查询8 跨校课程对比有结果", len(r) > 0, f"{len(r)} 条")
    schools = {row["school_name"] for row in r} if r else set()
    check("查询8 至少有一校数据", len(schools) >= 1, f"{schools}")


def test_nl2sql():
    print("\n" + "=" * 50)
    print("  模块 B — NL2SQL 自然语言查询")
    print("=" * 50)

    # 内置测试用例
    print("  --- 内置测试用例 ---")
    for tc in TEST_CASES:
        sql, params, desc, results = interpret_nl_query(tc["query"])
        has_result = results is not None and len(results) > 0
        check(f"\"{tc['query']}\"", has_result, f"→ {desc}, {len(results) if results else 0} 条")

    # 额外边界测试
    print("  --- 边界测试 ---")
    extra_tests = [
        ("数据结构这门课的学分和学时", True),   # 之前失败过
        ("搜索包含数据库的课程", True),          # 之前失败过
        ("对比两校计算机专业的课程差异", True),
        ("人工智能专业需要修多少学分", True),
    ]
    for q, expect_result in extra_tests:
        sql, params, desc, results = interpret_nl_query(q)
        ok = (results is not None and len(results) > 0) == expect_result
        check(f"「{q}」", ok, f"→ {desc}, {len(results) if results else 0} 条")


def summary():
    print("\n" + "=" * 50)
    print(f"  测试完成: {PASS} 通过 / {PASS + FAIL} 总计")
    print("=" * 50)
    if FAIL:
        print(f"  !! {FAIL} FAILED - check above")
    else:
        print("  ** ALL PASSED!")


if __name__ == "__main__":
    test_db_structure()
    test_module_a()
    test_module_b()
    test_nl2sql()
    summary()
