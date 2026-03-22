from uuid import UUID
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.models.user import User
from src.models.enums import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, email: str, password: str, role: UserRole = UserRole.SUBMITTER) -> User:
        user = User(email=email, hashed_password=pwd_context.hash(password), role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
