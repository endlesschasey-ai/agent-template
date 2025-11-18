"""File upload API routes."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import io
from PIL import Image

from ...db import AsyncSessionLocal
from ...services import ChatService
from ...models.schema import FileUploadResponse
from ...config import settings
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    上传图片文件

    Args:
        file: 上传的文件（仅支持图片）
        session_id: 会话 ID

    Returns:
        文件上传响应
    """
    # 验证文件类型
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。仅支持图片文件。"
        )

    # 读取文件内容
    file_data = await file.read()
    file_size = len(file_data)

    # 验证文件大小
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # 验证图片格式（尝试打开图片）
    try:
        img = Image.open(io.BytesIO(file_data))
        img.verify()
    except Exception as e:
        logger.error(f"图片验证失败: {e}")
        raise HTTPException(status_code=400, detail="无效的图片文件")

    # 保存到数据库
    async with AsyncSessionLocal() as db:
        service = ChatService(db)

        # 验证会话是否存在
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 创建文件记录
        db_file = await service.create_file(
            session_id=session_id,
            filename=file.filename or "untitled.png",
            file_type=file.content_type or "image/png",
            file_size=file_size,
            file_data=file_data
        )

        logger.info(f"[upload] 文件上传成功: {db_file.file_id}, {db_file.filename}")

        return FileUploadResponse(
            file_id=db_file.file_id,
            filename=db_file.filename,
            file_type=db_file.file_type,
            file_size=db_file.file_size,
            uploaded_at=db_file.uploaded_at
        )
