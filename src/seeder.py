# src/seeder.py - Seed database with sample data from SWUFE training plans
from src.database import get_connection, init_database


def seed_swufe_data():
    """Seed SWUFE (西南财经大学) training plan data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # === SCHOOLS ===
    cursor.execute("INSERT OR IGNORE INTO schools (id, name, short_name) VALUES (1, '西南财经大学', 'SWUFE')")
    cursor.execute("INSERT OR IGNORE INTO schools (id, name, short_name) VALUES (2, '上海财经大学', 'SUFE')")
    
    # === COLLEGES ===
    colleges = [
        (1, 1, '计算机与人工智能学院', '11'),
        (2, 1, '管理科学与工程学院', '10'),
        (3, 1, '金融学院', '3'),
        (4, 1, '统计学院', '6'),
        (5, 1, '数学学院', '15'),
        (6, 1, '工商管理学院', '7'),
        (7, 1, '会计学院', '5'),
        (8, 1, '基础学科拔尖实验班', '1'),
    ]
    for c_id, s_id, name, code in colleges:
        cursor.execute("INSERT OR IGNORE INTO colleges (id, school_id, name, code) VALUES (?, ?, ?, ?)",
                      (c_id, s_id, name, code))
    
    # === MAJORS ===
    majors = [
        (1, 1, '计算机类（含计算机科学与技术、人工智能）', '大类招生', 155, '本科', '4年'),
        (2, 1, '计算机科学与技术', '普通', 155, '本科', '4年'),
        (3, 1, '人工智能', '普通', 155, '本科', '4年'),
        (4, 8, '计算机科学与技术（基础学科拔尖实验班）', '拔尖实验班', 155, '本科', '4年'),
        (5, 2, '管理科学与工程类', '大类招生', 155, '本科', '4年'),
        (6, 3, '金融学类', '大类招生', 158, '本科', '4年'),
        (7, 3, '金融工程', '普通', 158, '本科', '4年'),
        (8, 4, '统计学类', '大类招生', 155, '本科', '4年'),
        (9, 5, '金融数学', '普通', 155, '本科', '4年'),
        (10, 2, '信息管理与信息系统', '普通', 155, '本科', '4年'),
        (11, 6, '工商管理类', '大类招生', 155, '本科', '4年'),
        (12, 7, '会计学', '普通', 155, '本科', '4年'),
    ]
    for m_id, col_id, name, mtype, credits, level, dur in majors:
        cursor.execute("""
            INSERT OR IGNORE INTO majors (id, college_id, name, major_type, total_credits, education_level, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (m_id, col_id, name, mtype, credits, level, dur))
    
    # === COURSES ===
    # 通识课程
    courses = [
        # (code, name, credits, total_hours, lecture_hours, practice_hours, assessment)
        ("TS101", '思想政治与法治', 3, 48, 40, 8, '考试'),
        ("TS102", '中国近现代史纲要', 3, 48, 40, 8, '考试'),
        ("TS103", '马克思主义基本原理', 3, 48, 40, 8, '考试'),
        ("TS104", '毛泽东思想和中国特色社会主义理论体系概论', 5, 80, 64, 16, '考试'),
        ("TS105", '形势与政策', 2, 32, 32, 0, '考查'),
        ("TS106", '大学英语I', 4, 64, 48, 16, '考试'),
        ("TS107", '大学英语II', 4, 64, 48, 16, '考试'),
        ("TS108", '大学英语III', 2, 32, 24, 8, '考试'),
        ("TS109", '大学体育I', 1, 32, 4, 28, '考查'),
        ("TS110", '大学体育II', 1, 32, 4, 28, '考查'),
        ("TS111", '大学体育III', 1, 32, 4, 28, '考查'),
        ("TS112", '大学体育IV', 1, 32, 4, 28, '考查'),
        ("TS113", '大学生心理健康与职业规划', 1, 16, 16, 0, '考查'),
        ("TS114", '军事理论', 2, 32, 32, 0, '考查'),
        ("TS115", '劳动教育', 1, 16, 8, 8, '考查'),
        ("TS116", '通识选修课', 6, 96, 96, 0, '考查'),
        
        # 数学基础
        ("MA101", '微积分I', 5, 80, 80, 0, '考试'),
        ("MA102", '微积分II', 5, 80, 80, 0, '考试'),
        ("MA103", '线性代数', 3, 48, 48, 0, '考试'),
        ("MA104", '概率论与数理统计', 4, 64, 56, 8, '考试'),
        
        # 计算机专业基础
        ("CS101", '程序设计基础', 4, 64, 40, 24, '考试'),
        ("CS102", '面向对象程序设计（C++）', 4, 64, 40, 24, '考试'),
        ("CS103", '数据结构', 4, 64, 48, 16, '考试'),
        ("CS104", '计算机组成原理', 4, 64, 48, 16, '考试'),
        ("CS105", '操作系统', 4, 64, 48, 16, '考试'),
        ("CS106", '计算机网络', 4, 64, 48, 16, '考试'),
        ("CS107", '数据库原理与应用', 4, 64, 48, 16, '考试'),
        ("CS108", '算法设计与分析', 3, 48, 40, 8, '考试'),
        ("CS109", '软件工程', 3, 48, 40, 8, '考试'),
        ("CS110", '编译原理', 3, 48, 40, 8, '考试'),
        
        # 人工智能方向
        ("AI101", '机器学习', 3, 48, 40, 8, '考试'),
        ("AI102", '深度学习', 3, 48, 36, 12, '考试'),
        ("AI103", '自然语言处理', 2, 32, 24, 8, '考试'),
        ("AI104", '计算机视觉', 2, 32, 24, 8, '考试'),
        ("AI105", '智能机器人', 2, 32, 24, 8, '考查'),
        
        # 专业选修
        ("SE101", 'Web前端开发技术', 3, 48, 32, 16, '考查'),
        ("SE102", 'Python数据分析', 3, 48, 32, 16, '考查'),
        ("SE103", '信息安全技术', 2, 32, 24, 8, '考查'),
        ("SE104", '云计算与大数据', 2, 32, 24, 8, '考查'),
        ("SE105", '区块链技术', 2, 32, 24, 8, '考查'),
        ("SE106", '移动应用开发', 3, 48, 32, 16, '考查'),
        
        # 数学/统计
        ("MA201", '离散数学', 4, 64, 64, 0, '考试'),
        ("MA202", '数值分析', 3, 48, 40, 8, '考试'),
        
        # 管理科学
        ("MG101", '管理学原理', 3, 48, 48, 0, '考试'),
        ("MG102", '运筹学', 4, 64, 56, 8, '考试'),
        ("MG103", '管理信息系统', 3, 48, 36, 12, '考试'),
        ("MG104", '数据分析与决策', 3, 48, 32, 16, '考试'),
        
        # 经济金融
        ("EC101", '政治经济学', 3, 48, 48, 0, '考试'),
        ("EC102", '微观经济学', 3, 48, 48, 0, '考试'),
        ("EC103", '宏观经济学', 3, 48, 48, 0, '考试'),
        ("EC104", '计量经济学', 3, 48, 40, 8, '考试'),
        ("FN101", '金融学', 3, 48, 48, 0, '考试'),
        ("FN102", '金融风险管理', 3, 48, 40, 8, '考试'),
        ("FN103", '投资学', 3, 48, 40, 8, '考试'),
        ("FN104", '公司金融', 3, 48, 40, 8, '考试'),
        ("FN105", '国际金融', 3, 48, 48, 0, '考试'),
        
        # 统计
        ("ST101", '统计学', 3, 48, 40, 8, '考试'),
        ("ST102", '时间序列分析', 3, 48, 36, 12, '考试'),
        ("ST103", '多元统计分析', 3, 48, 36, 12, '考试'),
        ("ST104", '数据挖掘', 3, 48, 32, 16, '考查'),
        
        # 实践环节
        ("PR101", '程序设计实践', 2, 32, 0, 32, '考查'),
        ("PR102", '专业实习', 4, 64, 0, 64, '考查'),
        ("PR103", '毕业设计（论文）', 8, 128, 0, 128, '考查'),
        ("PR104", '毕业实习', 4, 64, 0, 64, '考查'),
        
        # 工商管理
        ("BM101", '市场营销学', 3, 48, 48, 0, '考试'),
        ("BM102", '人力资源管理', 3, 48, 48, 0, '考试'),
        ("BM103", '财务管理', 3, 48, 40, 8, '考试'),
        ("BM104", '战略管理', 3, 48, 48, 0, '考试'),
        ("BM105", '组织行为学', 3, 48, 48, 0, '考试'),
        
        # 会计学
        ("AC101", '会计学基础', 3, 48, 48, 0, '考试'),
        ("AC102", '中级财务会计', 4, 64, 56, 8, '考试'),
        ("AC103", '成本会计', 3, 48, 40, 8, '考试'),
        ("AC104", '审计学', 3, 48, 40, 8, '考试'),
        ("AC105", '高级财务会计', 3, 48, 40, 8, '考试'),
        
        # 英语
        ("EN101", '学术英语', 2, 32, 24, 8, '考试'),
    ]
    inserted_courses = {}
    for code, name, credits, tot_h, lec_h, prac_h, assess in courses:
        cursor.execute("""
            INSERT OR IGNORE INTO courses (code, name, credits, total_hours, lecture_hours, practice_hours, assessment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, name, credits, tot_h, lec_h, prac_h, assess))
        # Get the course id
        cursor.execute("SELECT id FROM courses WHERE code = ?", (code,))
        row = cursor.fetchone()
        if row:
            inserted_courses[code] = row["id"]
    
    # === MAJOR_COURSES ===
    # Helper: map major name to id
    cursor.execute("SELECT id, name FROM majors")
    major_map = {row["name"]: row["id"] for row in cursor.fetchall()}
    cursor.execute("SELECT id, code FROM courses")
    course_map = {row["code"]: row["id"] for row in cursor.fetchall()}
    
    def mc(major_name, course_code, course_type, semester, weekly_hours=0, notes=""):
        mid = major_map.get(major_name)
        cid = course_map.get(course_code)
        if mid and cid:
            cursor.execute("""
                INSERT OR IGNORE INTO major_courses (major_id, course_id, course_type, semester, weekly_hours, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mid, cid, course_type, semester, weekly_hours, notes))
    
    # === 计算机科学与技术 培养方案 ===
    cs_major = '计算机科学与技术'
    # 通识必修
    mc(cs_major, 'TS101', '通识必修', 1, 3)
    mc(cs_major, 'TS102', '通识必修', 2, 3)
    mc(cs_major, 'TS103', '通识必修', 3, 3)
    mc(cs_major, 'TS104', '通识必修', 4, 5)
    mc(cs_major, 'TS105', '通识必修', 1, 1)
    mc(cs_major, 'TS106', '通识必修', 1, 4)
    mc(cs_major, 'TS107', '通识必修', 2, 4)
    mc(cs_major, 'TS108', '通识必修', 3, 2)
    mc(cs_major, 'TS109', '通识必修', 1, 2)
    mc(cs_major, 'TS110', '通识必修', 2, 2)
    mc(cs_major, 'TS111', '通识必修', 3, 2)
    mc(cs_major, 'TS112', '通识必修', 4, 2)
    mc(cs_major, 'TS113', '通识必修', 1, 1)
    mc(cs_major, 'TS114', '通识必修', 1, 2)
    mc(cs_major, 'TS115', '通识必修', 2, 1)
    mc(cs_major, 'TS116', '通识选修', 3, 3)
    
    # 数学基础
    mc(cs_major, 'MA101', '学科基础必修', 1, 5)
    mc(cs_major, 'MA102', '学科基础必修', 2, 5)
    mc(cs_major, 'MA103', '学科基础必修', 1, 3)
    mc(cs_major, 'MA104', '学科基础必修', 3, 4)
    mc(cs_major, 'MA201', '学科基础必修', 2, 4)
    
    # 专业核心必修
    mc(cs_major, 'CS101', '专业必修', 1, 4)
    mc(cs_major, 'CS102', '专业必修', 2, 4)
    mc(cs_major, 'CS103', '专业必修', 3, 4)
    mc(cs_major, 'CS104', '专业必修', 3, 4)
    mc(cs_major, 'CS105', '专业必修', 4, 4)
    mc(cs_major, 'CS106', '专业必修', 4, 4)
    mc(cs_major, 'CS107', '专业必修', 4, 4)
    mc(cs_major, 'CS108', '专业必修', 5, 3)
    mc(cs_major, 'CS109', '专业必修', 5, 3)
    mc(cs_major, 'CS110', '专业必修', 5, 3)
    
    # 专业选修
    mc(cs_major, 'AI101', '专业选修', 5, 3)
    mc(cs_major, 'AI102', '专业选修', 6, 3)
    mc(cs_major, 'SE101', '专业选修', 4, 3)
    mc(cs_major, 'SE102', '专业选修', 5, 3)
    mc(cs_major, 'SE103', '专业选修', 6, 2)
    mc(cs_major, 'SE104', '专业选修', 6, 2)
    mc(cs_major, 'SE105', '专业选修', 7, 2)
    mc(cs_major, 'SE106', '专业选修', 5, 3)
    mc(cs_major, 'AI103', '专业选修', 6, 2)
    mc(cs_major, 'AI104', '专业选修', 7, 2)
    mc(cs_major, 'MA202', '专业选修', 5, 3)
    
    # 英语
    mc(cs_major, 'EN101', '专业选修', 3, 2)
    
    # 实践环节
    mc(cs_major, 'PR101', '实践必修', 2, 2, notes="集中实践")
    mc(cs_major, 'PR102', '实践必修', 6, 4, notes="暑期实习")
    mc(cs_major, 'PR103', '实践必修', 8, 8, notes="毕业论文")
    mc(cs_major, 'PR104', '实践必修', 8, 4, notes="毕业实习")
    
    # === 人工智能 专业 ===
    ai_major = '人工智能'
    # Same 通识 + 数学 as CS
    mc(ai_major, 'TS101', '通识必修', 1, 3)
    mc(ai_major, 'TS102', '通识必修', 2, 3)
    mc(ai_major, 'TS103', '通识必修', 3, 3)
    mc(ai_major, 'TS104', '通识必修', 4, 5)
    mc(ai_major, 'TS105', '通识必修', 1, 1)
    mc(ai_major, 'TS106', '通识必修', 1, 4)
    mc(ai_major, 'TS107', '通识必修', 2, 4)
    mc(ai_major, 'TS108', '通识必修', 3, 2)
    mc(ai_major, 'TS109', '通识必修', 1, 2)
    mc(ai_major, 'TS110', '通识必修', 2, 2)
    mc(ai_major, 'TS111', '通识必修', 3, 2)
    mc(ai_major, 'TS112', '通识必修', 4, 2)
    mc(ai_major, 'TS113', '通识必修', 1, 1)
    mc(ai_major, 'TS114', '通识必修', 1, 2)
    mc(ai_major, 'TS115', '通识必修', 2, 1)
    mc(ai_major, 'TS116', '通识选修', 3, 3)
    mc(ai_major, 'MA101', '学科基础必修', 1, 5)
    mc(ai_major, 'MA102', '学科基础必修', 2, 5)
    mc(ai_major, 'MA103', '学科基础必修', 1, 3)
    mc(ai_major, 'MA104', '学科基础必修', 3, 4)
    mc(ai_major, 'MA201', '学科基础必修', 2, 4)
    mc(ai_major, 'CS101', '专业必修', 1, 4)
    mc(ai_major, 'CS102', '专业必修', 2, 4)
    mc(ai_major, 'CS103', '专业必修', 3, 4)
    mc(ai_major, 'CS104', '专业必修', 3, 4)
    mc(ai_major, 'CS107', '专业必修', 4, 4)
    mc(ai_major, 'CS108', '专业必修', 5, 3)
    mc(ai_major, 'AI101', '专业必修', 4, 3)
    mc(ai_major, 'AI102', '专业必修', 5, 3)
    mc(ai_major, 'AI103', '专业必修', 5, 2)
    mc(ai_major, 'AI104', '专业必修', 6, 2)
    mc(ai_major, 'AI105', '专业选修', 6, 2)
    mc(ai_major, 'CS105', '专业必修', 4, 4)
    mc(ai_major, 'CS106', '专业必修', 5, 4)
    mc(ai_major, 'CS109', '专业必修', 6, 3)
    mc(ai_major, 'SE102', '专业选修', 5, 3)
    mc(ai_major, 'SE104', '专业选修', 6, 2)
    mc(ai_major, 'PR101', '实践必修', 2, 2)
    mc(ai_major, 'PR102', '实践必修', 6, 4)
    mc(ai_major, 'PR103', '实践必修', 8, 8)
    mc(ai_major, 'PR104', '实践必修', 8, 4)
    
    # === 金融学类 ===
    fin_major = '金融学类'
    mc(fin_major, 'TS101', '通识必修', 1, 3)
    mc(fin_major, 'TS102', '通识必修', 2, 3)
    mc(fin_major, 'TS103', '通识必修', 3, 3)
    mc(fin_major, 'TS104', '通识必修', 4, 5)
    mc(fin_major, 'TS106', '通识必修', 1, 4)
    mc(fin_major, 'TS107', '通识必修', 2, 4)
    mc(fin_major, 'TS109', '通识必修', 1, 2)
    mc(fin_major, 'TS110', '通识必修', 2, 2)
    mc(fin_major, 'MA101', '学科基础必修', 1, 5)
    mc(fin_major, 'MA102', '学科基础必修', 2, 5)
    mc(fin_major, 'MA103', '学科基础必修', 1, 3)
    mc(fin_major, 'MA104', '学科基础必修', 3, 4)
    mc(fin_major, 'EC101', '学科基础必修', 1, 3)
    mc(fin_major, 'EC102', '学科基础必修', 2, 3)
    mc(fin_major, 'EC103', '学科基础必修', 3, 3)
    mc(fin_major, 'EC104', '学科基础必修', 4, 3)
    mc(fin_major, 'FN101', '专业必修', 3, 3)
    mc(fin_major, 'FN102', '专业必修', 4, 3)
    mc(fin_major, 'FN103', '专业必修', 4, 3)
    mc(fin_major, 'FN104', '专业必修', 5, 3)
    mc(fin_major, 'FN105', '专业必修', 5, 3)
    mc(fin_major, 'ST101', '专业必修', 3, 3)
    mc(fin_major, 'ST102', '专业选修', 5, 3)
    mc(fin_major, 'ST104', '专业选修', 6, 3)
    mc(fin_major, 'CS107', '专业选修', 5, 3)
    mc(fin_major, 'PR103', '实践必修', 8, 8)
    
    # === 计算机类（大类招生）===
    cs_class = '计算机类（含计算机科学与技术、人工智能）'
    mc(cs_class, 'MA101', '学科基础必修', 1, 5)
    mc(cs_class, 'MA102', '学科基础必修', 2, 5)
    mc(cs_class, 'MA103', '学科基础必修', 1, 3)
    mc(cs_class, 'MA104', '学科基础必修', 3, 4)
    mc(cs_class, 'MA201', '学科基础必修', 2, 4)
    mc(cs_class, 'CS101', '专业必修', 1, 4)
    mc(cs_class, 'CS102', '专业必修', 2, 4)
    mc(cs_class, 'CS103', '专业必修', 3, 4)
    mc(cs_class, 'CS104', '专业必修', 3, 4)
    mc(cs_class, 'CS105', '专业必修', 4, 4)
    mc(cs_class, 'CS106', '专业必修', 4, 4)
    mc(cs_class, 'CS107', '专业必修', 4, 4)
    mc(cs_class, 'TS101', '通识必修', 1, 3)
    mc(cs_class, 'TS106', '通识必修', 1, 4)
    mc(cs_class, 'TS107', '通识必修', 2, 4)
    mc(cs_class, 'PR103', '实践必修', 8, 8)

    # === 计算机科学与技术（拔尖实验班）===
    cs_elite = '计算机科学与技术（基础学科拔尖实验班）'
    # 通识必修（与普通班一致）
    mc(cs_elite, 'TS101', '通识必修', 1, 3)
    mc(cs_elite, 'TS102', '通识必修', 2, 3)
    mc(cs_elite, 'TS103', '通识必修', 3, 3)
    mc(cs_elite, 'TS104', '通识必修', 4, 5)
    mc(cs_elite, 'TS105', '通识必修', 1, 1)
    mc(cs_elite, 'TS106', '通识必修', 1, 4)
    mc(cs_elite, 'TS107', '通识必修', 2, 4)
    mc(cs_elite, 'TS108', '通识必修', 3, 2)
    mc(cs_elite, 'TS109', '通识必修', 1, 2)
    mc(cs_elite, 'TS110', '通识必修', 2, 2)
    mc(cs_elite, 'TS111', '通识必修', 3, 2)
    mc(cs_elite, 'TS112', '通识必修', 4, 2)
    mc(cs_elite, 'TS113', '通识必修', 1, 1)
    mc(cs_elite, 'TS114', '通识必修', 1, 2)
    mc(cs_elite, 'TS115', '通识必修', 2, 1)
    mc(cs_elite, 'TS116', '通识选修', 3, 3)
    # 数学基础
    mc(cs_elite, 'MA101', '学科基础必修', 1, 5)
    mc(cs_elite, 'MA102', '学科基础必修', 2, 5)
    mc(cs_elite, 'MA103', '学科基础必修', 1, 3)
    mc(cs_elite, 'MA104', '学科基础必修', 3, 4)
    mc(cs_elite, 'MA201', '学科基础必修', 2, 4)
    # 专业核心必修
    mc(cs_elite, 'CS101', '专业必修', 1, 4)
    mc(cs_elite, 'CS102', '专业必修', 2, 4)
    mc(cs_elite, 'CS103', '专业必修', 3, 4)
    mc(cs_elite, 'CS104', '专业必修', 3, 4)
    mc(cs_elite, 'CS105', '专业必修', 4, 4)
    mc(cs_elite, 'CS106', '专业必修', 4, 4)
    mc(cs_elite, 'CS107', '专业必修', 4, 4)
    mc(cs_elite, 'CS108', '专业必修', 5, 3)
    mc(cs_elite, 'CS109', '专业必修', 5, 3)
    mc(cs_elite, 'CS110', '专业必修', 5, 3)
    # 拔尖班特色：AI 方向比普通班更深
    mc(cs_elite, 'AI101', '专业必修', 4, 3)
    mc(cs_elite, 'AI102', '专业必修', 5, 3)
    mc(cs_elite, 'AI103', '专业选修', 6, 2)
    mc(cs_elite, 'AI104', '专业选修', 7, 2)
    # 专业选修
    mc(cs_elite, 'SE101', '专业选修', 4, 3)
    mc(cs_elite, 'SE102', '专业选修', 5, 3)
    mc(cs_elite, 'SE103', '专业选修', 6, 2)
    mc(cs_elite, 'SE104', '专业选修', 6, 2)
    mc(cs_elite, 'SE105', '专业选修', 7, 2)
    mc(cs_elite, 'SE106', '专业选修', 5, 3)
    mc(cs_elite, 'MA202', '专业选修', 5, 3)
    mc(cs_elite, 'EN101', '专业选修', 3, 2)
    # 实践环节
    mc(cs_elite, 'PR101', '实践必修', 2, 2)
    mc(cs_elite, 'PR102', '实践必修', 6, 4)
    mc(cs_elite, 'PR103', '实践必修', 8, 8)
    mc(cs_elite, 'PR104', '实践必修', 8, 4)

    # === 管理科学与工程类 ===
    mgmt_class = '管理科学与工程类'
    mc(mgmt_class, 'TS101', '通识必修', 1, 3)
    mc(mgmt_class, 'TS102', '通识必修', 2, 3)
    mc(mgmt_class, 'TS103', '通识必修', 3, 3)
    mc(mgmt_class, 'TS106', '通识必修', 1, 4)
    mc(mgmt_class, 'TS107', '通识必修', 2, 4)
    mc(mgmt_class, 'MA101', '学科基础必修', 1, 5)
    mc(mgmt_class, 'MA102', '学科基础必修', 2, 5)
    mc(mgmt_class, 'MA103', '学科基础必修', 1, 3)
    mc(mgmt_class, 'MA104', '学科基础必修', 3, 4)
    mc(mgmt_class, 'MG101', '专业必修', 3, 3)
    mc(mgmt_class, 'MG102', '专业必修', 4, 4)
    mc(mgmt_class, 'MG103', '专业必修', 5, 3)
    mc(mgmt_class, 'MG104', '专业必修', 5, 3)
    mc(mgmt_class, 'CS107', '专业选修', 5, 3)
    mc(mgmt_class, 'PR103', '实践必修', 8, 8)

    # === 金融工程 (SWUFE) ===
    fin_eng = '金融工程'
    mc(fin_eng, 'TS101', '通识必修', 1, 3)
    mc(fin_eng, 'TS102', '通识必修', 2, 3)
    mc(fin_eng, 'TS103', '通识必修', 3, 3)
    mc(fin_eng, 'TS106', '通识必修', 1, 4)
    mc(fin_eng, 'TS107', '通识必修', 2, 4)
    mc(fin_eng, 'MA101', '学科基础必修', 1, 5)
    mc(fin_eng, 'MA102', '学科基础必修', 2, 5)
    mc(fin_eng, 'MA103', '学科基础必修', 1, 3)
    mc(fin_eng, 'MA104', '学科基础必修', 3, 4)
    mc(fin_eng, 'EC101', '学科基础必修', 1, 3)
    mc(fin_eng, 'EC102', '学科基础必修', 2, 3)
    mc(fin_eng, 'FN101', '专业必修', 3, 3)
    mc(fin_eng, 'FN102', '专业必修', 4, 3)
    mc(fin_eng, 'FN103', '专业必修', 4, 3)
    mc(fin_eng, 'FN104', '专业必修', 5, 3)
    mc(fin_eng, 'FN105', '专业必修', 5, 3)
    mc(fin_eng, 'ST101', '专业必修', 3, 3)
    mc(fin_eng, 'PR103', '实践必修', 8, 8)

    # === 统计学类 ===
    stat_class = '统计学类'
    mc(stat_class, 'TS101', '通识必修', 1, 3)
    mc(stat_class, 'TS102', '通识必修', 2, 3)
    mc(stat_class, 'TS103', '通识必修', 3, 3)
    mc(stat_class, 'TS106', '通识必修', 1, 4)
    mc(stat_class, 'TS107', '通识必修', 2, 4)
    mc(stat_class, 'MA101', '学科基础必修', 1, 5)
    mc(stat_class, 'MA102', '学科基础必修', 2, 5)
    mc(stat_class, 'MA103', '学科基础必修', 1, 3)
    mc(stat_class, 'MA104', '学科基础必修', 3, 4)
    mc(stat_class, 'ST101', '专业必修', 3, 3)
    mc(stat_class, 'ST102', '专业必修', 4, 3)
    mc(stat_class, 'ST103', '专业必修', 5, 3)
    mc(stat_class, 'ST104', '专业选修', 5, 3)
    mc(stat_class, 'MA202', '专业选修', 5, 3)
    mc(stat_class, 'PR103', '实践必修', 8, 8)

    # === 金融数学 ===
    fin_math = '金融数学'
    mc(fin_math, 'TS101', '通识必修', 1, 3)
    mc(fin_math, 'TS102', '通识必修', 2, 3)
    mc(fin_math, 'TS103', '通识必修', 3, 3)
    mc(fin_math, 'TS106', '通识必修', 1, 4)
    mc(fin_math, 'TS107', '通识必修', 2, 4)
    mc(fin_math, 'MA101', '学科基础必修', 1, 5)
    mc(fin_math, 'MA102', '学科基础必修', 2, 5)
    mc(fin_math, 'MA103', '学科基础必修', 1, 3)
    mc(fin_math, 'MA104', '学科基础必修', 3, 4)
    mc(fin_math, 'MA201', '学科基础必修', 2, 4)
    mc(fin_math, 'MA202', '专业必修', 4, 3)
    mc(fin_math, 'EC101', '学科基础必修', 1, 3)
    mc(fin_math, 'EC102', '学科基础必修', 2, 3)
    mc(fin_math, 'FN101', '专业必修', 3, 3)
    mc(fin_math, 'FN103', '专业必修', 4, 3)
    mc(fin_math, 'ST101', '专业必修', 3, 3)
    mc(fin_math, 'ST102', '专业选修', 5, 3)
    mc(fin_math, 'PR103', '实践必修', 8, 8)

    # === 信息管理与信息系统 ===
    imis = '信息管理与信息系统'
    mc(imis, 'TS101', '通识必修', 1, 3)
    mc(imis, 'TS102', '通识必修', 2, 3)
    mc(imis, 'TS103', '通识必修', 3, 3)
    mc(imis, 'TS106', '通识必修', 1, 4)
    mc(imis, 'TS107', '通识必修', 2, 4)
    mc(imis, 'MA101', '学科基础必修', 1, 5)
    mc(imis, 'MA102', '学科基础必修', 2, 5)
    mc(imis, 'MA103', '学科基础必修', 1, 3)
    mc(imis, 'MA104', '学科基础必修', 3, 4)
    mc(imis, 'CS101', '专业必修', 1, 4)
    mc(imis, 'CS107', '专业必修', 4, 4)
    mc(imis, 'MG101', '专业必修', 3, 3)
    mc(imis, 'MG102', '专业必修', 4, 4)
    mc(imis, 'MG103', '专业必修', 5, 3)
    mc(imis, 'MG104', '专业必修', 5, 3)
    mc(imis, 'SE102', '专业选修', 5, 3)
    mc(imis, 'PR103', '实践必修', 8, 8)

    # === 工商管理类 ===
    biz_class = '工商管理类'
    mc(biz_class, 'TS101', '通识必修', 1, 3)
    mc(biz_class, 'TS102', '通识必修', 2, 3)
    mc(biz_class, 'TS103', '通识必修', 3, 3)
    mc(biz_class, 'TS106', '通识必修', 1, 4)
    mc(biz_class, 'TS107', '通识必修', 2, 4)
    mc(biz_class, 'MA101', '学科基础必修', 1, 5)
    mc(biz_class, 'MA102', '学科基础必修', 2, 5)
    mc(biz_class, 'EC101', '学科基础必修', 1, 3)
    mc(biz_class, 'EC102', '学科基础必修', 2, 3)
    mc(biz_class, 'MG101', '专业必修', 3, 3)
    mc(biz_class, 'BM101', '专业必修', 4, 3)
    mc(biz_class, 'BM102', '专业必修', 5, 3)
    mc(biz_class, 'BM103', '专业必修', 5, 3)
    mc(biz_class, 'BM104', '专业必修', 6, 3)
    mc(biz_class, 'BM105', '专业必修', 6, 3)
    mc(biz_class, 'ST101', '专业必修', 3, 3)
    mc(biz_class, 'PR103', '实践必修', 8, 8)

    # === 会计学 (SWUFE) ===
    swufe_acc = '会计学'
    mc(swufe_acc, 'TS101', '通识必修', 1, 3)
    mc(swufe_acc, 'TS102', '通识必修', 2, 3)
    mc(swufe_acc, 'TS103', '通识必修', 3, 3)
    mc(swufe_acc, 'TS106', '通识必修', 1, 4)
    mc(swufe_acc, 'TS107', '通识必修', 2, 4)
    mc(swufe_acc, 'MA101', '学科基础必修', 1, 5)
    mc(swufe_acc, 'MA102', '学科基础必修', 2, 5)
    mc(swufe_acc, 'MA103', '学科基础必修', 1, 3)
    mc(swufe_acc, 'EC101', '学科基础必修', 1, 3)
    mc(swufe_acc, 'EC102', '学科基础必修', 2, 3)
    mc(swufe_acc, 'AC101', '专业必修', 1, 3)
    mc(swufe_acc, 'AC102', '专业必修', 3, 4)
    mc(swufe_acc, 'AC103', '专业必修', 4, 3)
    mc(swufe_acc, 'AC104', '专业必修', 5, 3)
    mc(swufe_acc, 'AC105', '专业必修', 6, 3)
    mc(swufe_acc, 'BM103', '专业必修', 4, 3)
    mc(swufe_acc, 'FN101', '学科基础必修', 3, 3)
    mc(swufe_acc, 'ST101', '学科基础必修', 3, 3)
    mc(swufe_acc, 'PR103', '实践必修', 8, 8)

    conn.commit()
    conn.close()
    print("[OK] 数据填充完成！")


if __name__ == "__main__":
    print("初始化数据库...")
    init_database()
    print("填充数据...")
    seed_swufe_data()
