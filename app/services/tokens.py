from datetime import datetime
from sqlmodel import Session, select

from app.models.token import Token

def insert_token(token: Token, session: Session) -> Token:
    session.add(token)
    session.commit()
    session.refresh(token)
    
    return token

def get_token(token_id: int, session: Session) -> Token:
    return session.get(Token, token_id)

def get_token_by_user_id(user_id: int, session: Session) -> Token:
    query = select(Token).where(Token.user_id == user_id)
    token = session.exec(query).first()
    
    return token

def update_token(token_id: int, token: Token, session: Session) -> Token:
    db_token = session.get(Token, token_id)
    updates = token.model_dump(exclude_unset=True)
    db_token.sqlmodel_update(updates)
    session.add(db_token)
    session.commit()
    session.refresh(db_token)
    
    return db_token