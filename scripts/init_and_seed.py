#!/usr/bin/env python3
"""初始化数据库并填充数据 — 使用真实培养方案 PDF 导入"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.database import init_database

if __name__ == "__main__":
    print("=" * 50)
    print("  培养方案数据库系统 - 数据初始化")
    print("=" * 50)
    init_database()

    # Use real PDF data for SWUFE
    import importlib.util
    importer_path = os.path.join(os.path.dirname(__file__), "import_real_data.py")
    spec = importlib.util.spec_from_file_location("import_real_data", importer_path)
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)
    importer.import_all()

    # Add SUFE data for cross-school comparison
    from src.sufe_seeder import seed_sufe_data
    seed_sufe_data()

    print("\n[OK] 初始化完成！")
    print("  python run.py              # 交互模式")
    print("  python run.py 1 \"计算机类\"  # 查询必修课（真实数据）")
