# -*- coding: utf-8 -*-
"""
NL2SQL — LLM 驱动版本（可选）

使用方法：
  1. 设置环境变量 LLM_API_KEY（兼容 OpenAI / DeepSeek / 智谱 等）
  2. 可选：设置 LLM_BASE_URL（默认 https://api.openai.com/v1）
  3. 可选：设置 LLM_MODEL（默认 gpt-4o-mini）

  不设置 API Key 时自动回退到规则匹配（nl2sql.py）。

Prompt 设计思路
===============
采用 Few-shot + Schema-aware 策略：
1. 将数据库 Schema（表名、字段、关系）作为 System Prompt 注入
2. 提供 5 个精心设计的查询示例（覆盖 6 类查询）
3. 要求 LLM 输出结构化 JSON（包含 sql、params、description）
4. 仅允许 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP
5. 参数化查询使用 ? 占位符，params 按顺序排列

模型选择建议：
- 中文场景推荐 DeepSeek-V3 / Qwen-Max / GLM-4
- 轻量场景可用 gpt-4o-mini / DeepSeek-V2.5
"""

import os
import json
import re
from src.database import get_connection

# ── Schema Description (injected into system prompt) ──────────────
SCHEMA_DESC = """
你是一个 SQL 查询生成助手。你只能生成 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP。

## 数据库 Schema（SQLite）

### 表结构
- schools(id, name, short_name) — 学校，目前有：西南财经大学(SWUFE)、上海财经大学(SUFE)
- colleges(id, school_id FK→schools.id, name, code) — 学院
- majors(id, college_id FK→colleges.id, name, major_type, total_credits, education_level, duration) — 专业
- courses(id, code, name, credits, total_hours, lecture_hours, practice_hours, assessment_method) — 课程
- major_courses(id, major_id FK→majors.id, course_id FK→courses.id, course_type, semester, weekly_hours, notes) — 专业-课程关联

### 课程类型（major_courses.course_type）包含：
通识必修、通识选修、学科基础必修、专业必修、专业选修、实践必修、限选

### 学校名称
- 查询中"我校"或"西财"均指"西南财经大学"
- "上财"指"上海财经大学"
- "两校"指两所学校都查

## 查询类型参考

1. 必修课列表：查询某专业的必修课（course_type LIKE '%必修%'），返回课程代码、名称、学分、学时、考核方式、学期
2. 课程信息：查询某门课程（name LIKE '%关键词%'），返回代码、名称、学分、总学时、讲授学时、实践学时、考核方式
3. 总学分要求：查询某专业的总学分（majors.total_credits），同时 SUM(courses.credits) 计算实际累计
4. 开设课程的专业：查询某门课程被哪些专业开设（DISTINCT major_name）
5. 学院概览：查询某学院下所有专业的名称、学分、课程数
6. 模糊搜索：按关键词搜索课程（name LIKE '%关键词%'），返回代码、名称、学分
7. 跨校对比：查询相同专业在两所学校的数据，按 school 分组

## 输出格式

严格按以下 JSON 格式输出，不要输出任何其他内容：
{"sql": "SELECT ...", "params": ["param1", "param2"], "description": "中文描述"}
"""

FEW_SHOT_EXAMPLES = """
## 示例

Q: 查询计算机科学与技术的必修课有哪些
A: {"sql": "SELECT c.code, c.name, c.credits, c.total_hours, c.assessment_method, mc.semester, mc.course_type FROM major_courses mc JOIN courses c ON mc.course_id = c.id JOIN majors m ON mc.major_id = m.id WHERE m.name = ? AND mc.course_type LIKE '%必修%' ORDER BY mc.semester, c.code", "params": ["计算机科学与技术"], "description": "计算机科学与技术 的必修课列表"}

Q: 数据结构这门课的学分和学时是多少
A: {"sql": "SELECT c.code, c.name, c.credits, c.total_hours, c.lecture_hours, c.practice_hours, c.assessment_method FROM courses c WHERE c.name LIKE ?", "params": ["%数据结构%"], "description": "课程「数据结构」的详细信息"}

Q: 金融学专业的总学分要求
A: {"sql": "SELECT m.name, m.total_credits, m.duration, (SELECT SUM(c2.credits) FROM major_courses mc2 JOIN courses c2 ON mc2.course_id = c2.id WHERE mc2.major_id = m.id) as actual_credits FROM majors m WHERE m.name = ?", "params": ["金融学"], "description": "金融学 的学分要求"}

Q: 数据库原理与应用被哪些专业开设
A: {"sql": "SELECT DISTINCT m.name as major_name, col.name as college_name, s.name as school_name, mc.course_type, mc.semester FROM major_courses mc JOIN courses c ON mc.course_id = c.id JOIN majors m ON mc.major_id = m.id JOIN colleges col ON m.college_id = col.id JOIN schools s ON col.school_id = s.id WHERE c.name LIKE ? ORDER BY s.name, col.name, m.name", "params": ["%数据库原理与应用%"], "description": "开设「数据库原理与应用」的所有专业"}

Q: 计算机学院有哪些专业
A: {"sql": "SELECT m.name as major_name, m.major_type, m.total_credits, (SELECT COUNT(*) FROM major_courses mc2 WHERE mc2.major_id = m.id) as course_count FROM majors m JOIN colleges c ON m.college_id = c.id WHERE c.name LIKE ? ORDER BY m.name", "params": ["%计算机%"], "description": "计算机学院的专业概览"}
"""


def interpret_with_llm(user_query):
    """
    Use LLM to convert natural language to SQL.
    Falls back to rule-based if no API key or LLM error.
    Returns (sql, params, description, results) or None to fall back.
    """
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        return None

    try:
        import urllib.request

        messages = [
            {"role": "system", "content": SCHEMA_DESC + "\n" + FEW_SHOT_EXAMPLES},
            {"role": "user", "content": f"Q: {user_query}\nA:"},
        ]

        req_body = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 800,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=req_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
        else:
            parsed = json.loads(content)

        sql = parsed.get("sql", "")
        params = parsed.get("params", [])
        description = parsed.get("description", "LLM 生成查询")

        # Safety: only allow SELECT
        if not sql.strip().upper().startswith("SELECT"):
            return None

        # Execute
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        results = [dict(r) for r in cursor.fetchall()]
        conn.close()

        return sql, params, description, results

    except Exception as e:
        import sys
        print(f"[NL2SQL-LLM] LLM query failed, falling back to rule-based: {e}", file=sys.stderr)
        return None
