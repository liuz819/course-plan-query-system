# src/database.py - Database connection and schema management
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "training.db"


def get_connection():
    """Get a database connection."""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Create all tables with proper schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        -- ============================================
        -- 学校表
        -- ============================================
        CREATE TABLE IF NOT EXISTS schools (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,          -- 学校全称
            short_name  TEXT NOT NULL,          -- 简称
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ============================================
        -- 学院表
        -- ============================================
        CREATE TABLE IF NOT EXISTS colleges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id   INTEGER NOT NULL REFERENCES schools(id),
            name        TEXT NOT NULL,          -- 学院名称
            code        TEXT,                   -- 学院编号（如"11"）
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(school_id, name)
        );

        -- ============================================
        -- 专业表
        -- ============================================
        CREATE TABLE IF NOT EXISTS majors (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id      INTEGER NOT NULL REFERENCES colleges(id),
            name            TEXT NOT NULL,          -- 专业名称
            major_type      TEXT DEFAULT '普通',    -- 类型：普通/实验班/双学位等
            total_credits   REAL,                   -- 最低毕业学分要求
            education_level TEXT DEFAULT '本科',    -- 培养层次
            duration        TEXT DEFAULT '4年',      -- 学制
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(college_id, name)
        );

        -- ============================================
        -- 课程表
        -- ============================================
        CREATE TABLE IF NOT EXISTS courses (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            code              TEXT,                   -- 课程号
            name              TEXT NOT NULL,          -- 课程名称
            credits           REAL NOT NULL,          -- 学分
            total_hours       REAL,                   -- 总学时
            lecture_hours     REAL,                   -- 讲授学时
            practice_hours    REAL,                   -- 实践/实验学时
            assessment_method TEXT,                   -- 考核方式：考试/考查
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code)
        );

        -- ============================================
        -- 专业-课程关联表（培养方案核心表）
        -- ============================================
        CREATE TABLE IF NOT EXISTS major_courses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            major_id      INTEGER NOT NULL REFERENCES majors(id),
            course_id     INTEGER NOT NULL REFERENCES courses(id),
            course_type   TEXT NOT NULL,          -- 课程性质：必修/选修/通识必修/专业必修等
            semester      INTEGER,                -- 开课学期（1-8）
            weekly_hours  REAL,                   -- 周学时
            notes         TEXT,                   -- 备注
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(major_id, course_id)
        );

        -- ============================================
        -- 索引（加速查询）
        -- ============================================
        CREATE INDEX IF NOT EXISTS idx_colleges_school ON colleges(school_id);
        CREATE INDEX IF NOT EXISTS idx_majors_college ON majors(college_id);
        CREATE INDEX IF NOT EXISTS idx_major_courses_major ON major_courses(major_id);
        CREATE INDEX IF NOT EXISTS idx_major_courses_course ON major_courses(course_id);
        CREATE INDEX IF NOT EXISTS idx_courses_name ON courses(name);
    """)
    
    conn.commit()
    conn.close()
    print(f"[OK] 数据库初始化完成: {DB_PATH}")


if __name__ == "__main__":
    init_database()
