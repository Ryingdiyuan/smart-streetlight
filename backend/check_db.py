"""检查数据库里的用户"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
DB_FILE = backend_dir / "temp_db.sqlite3"
SQLITE_URL = f"sqlite:///{str(DB_FILE).replace(os.sep, '/')}"
database.engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
database.SessionLocal = sessionmaker(
    bind=database.engine, autoflush=False, autocommit=False, future=True
)

from app.models.user import User

db = database.SessionLocal()
print("=== 数据库中的所有用户 ===")
users = db.query(User).all()
for u in users:
    print(f"ID: {u.id}, 用户名: {u.username}, 密码哈希: {u.password_hash[:30]}..., 角色: {u.role}")

db.close()
