from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from conf.authentication import auth
from users.schemas import UserSchema
from users.models import User
from conf.database import get_db
from sqlmodel import Session, select

router = APIRouter()

@router.post("/create-user")
async def create_user(user: UserSchema, db: Session = Depends(get_db)):
    try:
        email = user.email
        password = user.password

        first_name = user.first_name
        last_name = user.last_name
        role = user.role

        verify_user = select(User).where(User.email == email)
        existing_user = db.exec(verify_user).first()

        if existing_user:
            return JSONResponse(content={"message": f"El usuario con email {email} ya existe"}, status_code=409)
        
        create_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        create_user.set_password(password)

        db.add(create_user)
        db.commit()
        db.refresh(create_user)
        return JSONResponse(content={"message": f"El usuario {email} ha sido creado exitosamente"}, status_code=201)
    
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(content={"message": f"Error al crear el usuario {e}"}, status_code=500)
        
@router.post("/login")
async def login(user_schema: UserSchema, db: Session = Depends(get_db)):
    try:
        email = user_schema.email
        password = user_schema.password

        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            return JSONResponse(content={"error": "No se encontró ningún usuario"}, status_code=401)
        
        if not user.verify_password(password):
            return JSONResponse(content={"error": "Credenciales inválidas"}, status_code=401)
        
        token_payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }
        
        return JSONResponse(content={
            "access_token": auth.create_access_token(token_payload),
            "refresh_token": auth.create_refresh_token(token_payload)
        })
        
    except Exception as e:
        print(f"Ha ocurrido un error interno al iniciar sesión {e}")
        return JSONResponse(content={"message": f"Ha ocurrido un error interno al iniciar sesión"}, status_code=500)
    
@router.get("/list-users")
async def list_users(db: Session = Depends(get_db)):
    try:
        users = list(db.exec(select(User).order_by(User.id)).all())
        
        users_list = []
        for u in users:
            user = dict(u)
            user.pop("password")
            users_list.append(user)
            
        return JSONResponse(content=jsonable_encoder(users_list), status_code=200)
    except Exception as e:
        print(f"Ha ocurrido un error interno al obtener la lista de usuarios {e}")
        return JSONResponse(content={"message": f"Ha ocurrido un error interno al obtener la lista de usuarios"}, status_code=500)
        