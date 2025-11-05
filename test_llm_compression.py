#!/usr/bin/env python3
"""
测试LLM驱动的压缩系统

对比规则方法和LLM方法的压缩效果
"""

import asyncio
import time
import os
from typing import List, Dict

# 设置环境变量（如果需要）
# os.environ["OPENAI_API_KEY"] = "your-api-key"
# os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

from hybrid_compressor import HybridCompressor


def create_test_messages() -> List[Dict]:
    """创建测试消息"""
    return [
        {
            "role": "user",
            "content": "我想创建一个Python Web应用，需要实现用户认证和文件上传功能",
            "timestamp": time.time() - 3000,
            "tokens": 30
        },
        {
            "role": "assistant",
            "content": """好的！我帮你设计一个基于FastAPI的Web应用。首先创建项目结构：

```bash
mkdir my_webapp
cd my_webapp
mkdir app templates static
```

然后创建主应用文件 `app/main.py`:

```python
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import uvicorn

app = FastAPI(title="My Web App")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    return {"message": "Welcome to My Web App"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

接下来需要实现用户认证系统。""",
            "timestamp": time.time() - 2800,
            "tokens": 200
        },
        {
            "role": "user",
            "content": "好的，继续实现用户认证部分，包括注册和登录",
            "timestamp": time.time() - 2600,
            "tokens": 25
        },
        {
            "role": "assistant",
            "content": """创建用户认证模块 `app/auth.py`:

```python
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

然后在 `app/main.py` 中添加认证路由：

```python
from app.auth import verify_password, get_password_hash, create_access_token

@app.post("/register")
async def register(username: str, password: str, email: str):
    # 检查用户是否存在
    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    # 创建新用户
    hashed_password = get_password_hash(password)
    users_db[username] = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password
    }
    return {"message": "User created successfully"}

@app.post("/login")
async def login(username: str, password: str):
    user = users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
```""",
            "timestamp": time.time() - 2400,
            "tokens": 400
        },
        {
            "role": "user",
            "content": "现在需要添加数据库支持，使用SQLite存储用户信息",
            "timestamp": time.time() - 2200,
            "tokens": 25
        },
        {
            "role": "assistant",
            "content": """好的，我们使用SQLAlchemy作为ORM。首先安装依赖：

```bash
pip install sqlalchemy aiosqlite
```

创建数据库模型 `app/models.py`:

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
```

更新 `app/auth.py` 中的用户操作函数：

```python
from app.models import UserModel, SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_username(db, username: str):
    return db.query(UserModel).filter(UserModel.username == username).first()

def create_user(db, username: str, email: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = UserModel(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```""",
            "timestamp": time.time() - 2000,
            "tokens": 350
        },
        {
            "role": "user",
            "content": "很好！现在遇到一个问题，文件上传时出现了错误：OSError: [Errno 28] No space left on device",
            "timestamp": time.time() - 1800,
            "tokens": 40
        },
        {
            "role": "assistant",
            "content": """这个错误表示磁盘空间不足。我们需要实现以下改进：

1. **添加文件大小限制**：

```python
from fastapi import File, UploadFile, HTTPException

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 检查文件大小
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # 保存文件
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    return {"filename": file.filename, "size": len(contents)}
```

2. **添加磁盘空间检查**：

```python
import shutil

def check_disk_space(path="/"):
    stat = shutil.disk_usage(path)
    free_gb = stat.free / (1024**3)
    return free_gb

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 检查剩余空间
    if check_disk_space() < 1:  # 少于1GB
        raise HTTPException(status_code=507, detail="Insufficient storage")

    # ... rest of the code
```

3. **实现文件清理策略**：

```python
import os
from datetime import datetime, timedelta

def cleanup_old_files(directory="uploads", days=7):
    now = datetime.now()
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        if now - file_modified > timedelta(days=days):
            os.remove(filepath)
            print(f"Deleted old file: {filename}")
```

这样可以有效避免磁盘空间问题。""",
            "timestamp": time.time() - 1600,
            "tokens": 350
        }
    ]


async def test_compression_comparison():
    """对比不同压缩方法"""
    print("=" * 80)
    print("🧪 LLM驱动压缩系统测试")
    print("=" * 80)
    print()

    # 创建测试消息
    messages = create_test_messages()

    print(f"📝 测试数据: {len(messages)} 条消息")
    total_tokens = sum(msg.get("tokens", 0) for msg in messages)
    print(f"   总Token数: {total_tokens:,}")
    print()

    # 测试1: 规则方法
    print("━" * 80)
    print("【测试1】规则方法（AU2）")
    print("━" * 80)

    compressor_rule = HybridCompressor(use_llm=False)
    result_rule = await compressor_rule.compress(messages)

    print(f"\n📊 规则方法结果:")
    print(f"   压缩率: {result_rule['compression_ratio']*100:.1f}%")
    print(f"   原始Tokens: {result_rule['original_tokens']:,}")
    print(f"   压缩后Tokens: {result_rule['compressed_tokens']:,}")
    print(f"   节省Tokens: {result_rule['original_tokens'] - result_rule['compressed_tokens']:,}")
    print(f"   耗时: {result_rule.get('elapsed_time', 0):.2f}秒")

    if result_rule.get('compressed_message'):
        content = result_rule['compressed_message'].get('content', '')
        print(f"\n📄 压缩摘要预览 (前500字符):")
        print(content[:500])
        if len(content) > 500:
            print("...")

    # 测试2: LLM方法
    print("\n\n━" * 80)
    print("【测试2】LLM方法")
    print("━" * 80)

    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  未设置API密钥，跳过LLM测试")
        print("   设置方法:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   或")
        print("   export ANTHROPIC_API_KEY='your-key'")
        return

    try:
        compressor_llm = HybridCompressor(use_llm=True, llm_threshold=1)
        result_llm = await compressor_llm.compress(messages, force_method="llm")

        print(f"\n📊 LLM方法结果:")
        print(f"   压缩率: {result_llm['compression_ratio']*100:.1f}%")
        print(f"   原始Tokens: {result_llm['original_tokens']:,}")
        print(f"   压缩后Tokens: {result_llm['compressed_tokens']:,}")
        print(f"   节省Tokens: {result_llm['original_tokens'] - result_llm['compressed_tokens']:,}")
        print(f"   输入Tokens: {result_llm.get('input_tokens', 0):,}")
        print(f"   输出Tokens: {result_llm.get('output_tokens', 0):,}")
        print(f"   成本: ${result_llm.get('cost', 0):.6f}")
        print(f"   耗时: {result_llm.get('elapsed_time', 0):.2f}秒")
        print(f"   模型: {result_llm.get('model', 'N/A')}")

        if result_llm.get('compressed_message'):
            content = result_llm['compressed_message'].get('content', '')
            print(f"\n📄 压缩摘要:")
            print(content)

        # 对比
        print("\n\n━" * 80)
        print("【对比分析】")
        print("━" * 80)

        rule_ratio = result_rule['compression_ratio']
        llm_ratio = result_llm['compression_ratio']

        print(f"\n压缩率对比:")
        print(f"   规则方法: {rule_ratio*100:.1f}%")
        print(f"   LLM方法:  {llm_ratio*100:.1f}%")
        print(f"   提升: {(llm_ratio - rule_ratio)*100:+.1f}%")

        print(f"\n成本分析:")
        print(f"   规则方法: $0.000000 (免费)")
        print(f"   LLM方法:  ${result_llm.get('cost', 0):.6f}")

        print(f"\n速度对比:")
        print(f"   规则方法: {result_rule.get('elapsed_time', 0):.2f}秒")
        print(f"   LLM方法:  {result_llm.get('elapsed_time', 0):.2f}秒")

    except Exception as e:
        print(f"\n❌ LLM测试失败: {e}")
        print("   这可能是因为API密钥未设置或配置不正确")

    # 测试3: 混合方法
    print("\n\n━" * 80)
    print("【测试3】混合方法（智能选择）")
    print("━" * 80)

    compressor_hybrid = HybridCompressor(use_llm=True, llm_threshold=5)

    # 少量消息（应该用规则）
    result_hybrid1 = await compressor_hybrid.compress(messages[:3])
    print(f"\n少量消息(3条): 使用 {result_hybrid1['method']} 方法")

    # 大量消息（应该用LLM）
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        try:
            result_hybrid2 = await compressor_hybrid.compress(messages)
            print(f"大量消息({len(messages)}条): 使用 {result_hybrid2['method']} 方法")
        except:
            print(f"大量消息({len(messages)}条): LLM不可用，回退到规则方法")

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_compression_comparison())
