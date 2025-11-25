from sqlmodel import SQLModel

class ChatMessage(SQLModel):
    message: str