from typing import List, Optional
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message

class ConversationService:
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    def create_conversation(self, user_id: str, title: str = "New Conversation") -> Conversation:
        return self.conversation_repository.create_conversation(user_id=user_id, title=title)

    def get_conversation_by_id(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        conversation = self.conversation_repository.get_conversation_by_id(conversation_id)
        # ISOLATION: Check if conversation exists and belongs to the user
        if conversation and conversation.user_id == user_id:
            return conversation
        return None

    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        return self.conversation_repository.get_conversations_by_user(user_id=user_id)

    def append_message(self, conversation_id: str, user_id: str, role: str, content: str) -> Optional[Message]:
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return None
        return self.conversation_repository.add_message(conversation_id=conversation_id, role=role, content=content)

    def get_messages(self, conversation_id: str, user_id: str) -> Optional[List[Message]]:
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return None
        return self.conversation_repository.get_messages(conversation_id=conversation_id)
        
    def commit(self):
        self.conversation_repository.db.commit()
        
    def rollback(self):
        self.conversation_repository.db.rollback()
