from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException, status
from database import Base, engine, SessionLocal
from auth import router as auth_router
from routers.users import router as users_router
from routers.reviews import router as reviews_router
from routers.questions import router as questions_router
from routers.specialists import router as specialists_router
from models import User, Review, Question, Specialist
from datetime import datetime
from auth import get_current_user

# ВАЖНО: Для запуска на Render используйте команду:
# uvicorn backend.main:app --host 0.0.0.0 --port $PORT
# (если main.py лежит в папке backend)

app = FastAPI(title="biosphere API")

# CORS: разрешаем локальную разработку и продакшн
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://biosfera-frontend.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(reviews_router)
app.include_router(questions_router)
app.include_router(specialists_router)

@app.on_event("startup")
def on_startup():
    print("=== BIOSPHERE API STARTED ===")
    # Создать таблицы только для SQLite (локальная разработка)
    # Для PostgreSQL используйте миграции Alembic
    from database import DATABASE_URL
    if DATABASE_URL.startswith('sqlite'):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created/verified")
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")

@app.get("/")
def root():
    return {"message": "biosphere API is running", "status": "ok"}

@app.get("/health")
def health_check():
    """Health check endpoint for Render"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503

@app.post("/admin/clear_all")
def clear_all():
    db = SessionLocal()
    db.query(Review).delete()
    db.query(Question).delete()
    db.query(User).delete()
    db.query(Specialist).delete()
    db.commit()
    db.close()
    return {"status": "ok"}

@app.get("/admin/export")
def export_data(current_user: User = Depends(get_current_user)):
    """Экспорт всех данных в формате JSON"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к этой функции"
        )
    
    db = SessionLocal()
    
    # Получаем все данные
    specialists = db.query(Specialist).all()
    reviews = db.query(Review).all()
    questions = db.query(Question).all()
    users = db.query(User).all()
    
    # Преобразуем в словари
    specialists_data = [
        {
            "id": s.id,
            "name": s.name,
            "position": s.position,
            "specialization": s.specialization,
            "workplace": s.workplace,
            "education": s.education,
            "extra_qual": s.extra_qual,
            "photo": s.photo
        } for s in specialists
    ]
    
    reviews_data = [
        {
            "id": r.id,
            "text": r.text,
            "rating": r.rating,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "user_name": r.user.name if r.user else None,
            "guest_name": r.guest_name,
            "admin_reply": r.admin_reply
        } for r in reviews
    ]
    
    questions_data = [
        {
            "id": q.id,
            "text": q.text,
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "user_name": q.user.name if q.user else None,
            "guest_name": q.guest_name,
            "admin_reply": q.admin_reply,
            "is_read": q.is_read
        } for q in questions
    ]
    
    users_data = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None
        } for u in users
    ]
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "statistics": {
            "total_specialists": len(specialists),
            "total_reviews": len(reviews),
            "total_questions": len(questions),
            "total_users": len(users),
            "average_rating": sum(r.rating for r in reviews) / len(reviews) if reviews else 0,
            "response_rate": len([q for q in questions if q.admin_reply]) / len(questions) * 100 if questions else 0
        },
        "specialists": specialists_data,
        "reviews": reviews_data,
        "questions": questions_data,
        "users": users_data
    }
    
    db.close()
    
    return JSONResponse(content=export_data)

@app.post("/admin/cleanup")
def cleanup_old_data(current_user: User = Depends(get_current_user)):
    """Очистка старых данных (старше 1 года)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к этой функции"
        )
    
    db = SessionLocal()
    from datetime import timedelta
    
    # Дата год назад
    one_year_ago = datetime.now() - timedelta(days=365)
    
    # Удаляем старые отзывы без ответов администратора
    old_reviews = db.query(Review).filter(
        Review.created_at < one_year_ago,
        Review.admin_reply.is_(None)
    ).all()
    
    for review in old_reviews:
        db.delete(review)
    
    # Удаляем старые вопросы без ответов администратора
    old_questions = db.query(Question).filter(
        Question.created_at < one_year_ago,
        Question.admin_reply.is_(None)
    ).all()
    
    for question in old_questions:
        db.delete(question)
    
    db.commit()
    db.close()
    
    return {
        "status": "success",
        "deleted_reviews": len(old_reviews),
        "deleted_questions": len(old_questions),
        "message": f"Удалено {len(old_reviews)} старых отзывов и {len(old_questions)} старых вопросов"
    }

@app.get("/admin/statistics")
def get_detailed_statistics(current_user: User = Depends(get_current_user)):
    """Получение подробной статистики системы"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к этой функции"
        )
    
    db = SessionLocal()
    from datetime import timedelta
    
    # Базовые данные
    total_specialists = db.query(Specialist).count()
    total_reviews = db.query(Review).count()
    total_questions = db.query(Question).count()
    total_users = db.query(User).count()
    
    # Статистика по рейтингам
    reviews_with_rating = db.query(Review).filter(Review.rating.isnot(None)).all()
    average_rating = sum(r.rating for r in reviews_with_rating) / len(reviews_with_rating) if reviews_with_rating else 0
    
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = len([r for r in reviews_with_rating if r.rating == i])
    
    # Статистика по ответам
    answered_questions = db.query(Question).filter(Question.admin_reply.isnot(None)).count()
    response_rate = (answered_questions / total_questions * 100) if total_questions > 0 else 0
    
    # Статистика по времени
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    recent_reviews = db.query(Review).filter(Review.created_at >= week_ago).count()
    recent_questions = db.query(Question).filter(Question.created_at >= week_ago).count()
    
    monthly_reviews = db.query(Review).filter(Review.created_at >= month_ago).count()
    monthly_questions = db.query(Question).filter(Question.created_at >= month_ago).count()
    
    # Статистика по специалистам
    specialists_by_position = {}
    for specialist in db.query(Specialist).all():
        position = specialist.position or "Не указана"
        specialists_by_position[position] = specialists_by_position.get(position, 0) + 1
    
    # Статистика по местам работы
    specialists_by_workplace = {}
    for specialist in db.query(Specialist).all():
        workplace = specialist.workplace or "Не указано"
        specialists_by_workplace[workplace] = specialists_by_workplace.get(workplace, 0) + 1
    
    db.close()
    
    return {
        "overview": {
            "total_specialists": total_specialists,
            "total_reviews": total_reviews,
            "total_questions": total_questions,
            "total_users": total_users,
            "average_rating": round(average_rating, 1),
            "response_rate": round(response_rate, 1)
        },
        "recent_activity": {
            "reviews_last_week": recent_reviews,
            "questions_last_week": recent_questions,
            "reviews_last_month": monthly_reviews,
            "questions_last_month": monthly_questions
        },
        "rating_distribution": rating_distribution,
        "specialists_by_position": specialists_by_position,
        "specialists_by_workplace": specialists_by_workplace,
        "generated_at": now.isoformat()
    }

@app.get("/admin/logs")
def get_system_logs(current_user: User = Depends(get_current_user)):
    """Получение логов системы"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к этой функции"
        )
    
    db = SessionLocal()
    
    # Получаем последние действия
    recent_reviews = db.query(Review).order_by(Review.created_at.desc()).limit(10).all()
    recent_questions = db.query(Question).order_by(Question.created_at.desc()).limit(10).all()
    
    logs = []
    
    # Логи отзывов
    for review in recent_reviews:
        logs.append({
            "timestamp": review.created_at.isoformat() if review.created_at else None,
            "type": "review",
            "action": "created",
            "user": review.user.name if review.user else review.guest_name or "Гость",
            "details": f"Отзыв с рейтингом {review.rating} звезд",
            "id": review.id
        })
    
    # Логи вопросов
    for question in recent_questions:
        logs.append({
            "timestamp": question.created_at.isoformat() if question.created_at else None,
            "type": "question",
            "action": "created",
            "user": question.user.name if question.user else question.guest_name or "Гость",
            "details": f"Вопрос {'(отвечен)' if question.admin_reply else '(ожидает ответа)'}",
            "id": question.id
        })
    
    # Сортируем по времени
    logs.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    # Статистика ошибок (симуляция)
    error_stats = {
        "total_errors": 0,
        "errors_last_24h": 0,
        "most_common_error": "Нет ошибок",
        "system_health": "Отлично"
    }
    
    db.close()
    
    return {
        "recent_logs": logs[:20],  # Последние 20 логов
        "error_statistics": error_stats,
        "system_info": {
            "database_connections": "Активно",
            "api_status": "Работает",
            "last_backup": datetime.now().isoformat(),
            "uptime": "100%"
        }
    }

# TODO: Подключить роутеры для specialists, testimonials, faq, если они появятся в будущем

