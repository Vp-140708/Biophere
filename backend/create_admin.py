from database import SessionLocal
from models import User
from auth import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        admin_email = "admin@biosphere.ru"
        admin_password = "ADMINBIO"
        
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            if existing_admin.email != admin_email:
                existing_admin.is_admin = False
                print(f"Убран статус админа у пользователя {existing_admin.email}")
        
        existing_user = db.query(User).filter(User.email == admin_email).first()
        
        if existing_user:
            existing_user.is_admin = True
            existing_user.password_hash = get_password_hash(admin_password)
            existing_user.name = "Admin"
            existing_user.phone = "0000000000"
            print(f"Обновлен существующий пользователь {admin_email} как админ")
        else:
            admin_user = User(
                name="Admin",
                email=admin_email,
                phone="0000000000",
                password_hash=get_password_hash(admin_password),
                is_admin=True
            )
            db.add(admin_user)
            print(f"Создан новый админ {admin_email}")
        
        db.commit()
        print(f"Админ {admin_email} успешно создан/обновлен")
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()

