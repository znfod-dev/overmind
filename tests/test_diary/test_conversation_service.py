
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime

from app.diary.services.conversation import ConversationService
from app.models import Conversation, Message, ConversationStatus, MessageRole

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def mock_db_session():
    """Provides a mock SQLAlchemy AsyncSession"""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    yield session

@pytest_asyncio.fixture
async def conversation_service(mock_db_session):
    """Provides a ConversationService instance with a mocked db session"""
    return ConversationService(mock_db_session)

async def test_start_conversation_creates_new_if_none_exists(
    conversation_service: ConversationService,
    mock_db_session: AsyncMock
):
    """
    Test that a new conversation is created when no active one exists for the given date.
    """
    user_id = 1
    entry_date = date(2023, 1, 15)

    # 1. Setup: Patch get_active_conversation to return None asynchronously
    with patch.object(conversation_service, 'get_active_conversation', new_callable=AsyncMock) as mock_get_active:
        mock_get_active.return_value = None

        # 2. Mock AI call (not essential for this test's logic, but good practice)
        # Let it fallback to default message on failure.

        # 3. Action: Call the service method
        conversation, initial_message = await conversation_service.start_conversation(
            user_id=user_id,
            entry_date=entry_date,
            timezone="UTC"
        )

        # 4. Assertions
        # Verify that get_active_conversation was called
        mock_get_active.assert_awaited_once_with(user_id, entry_date)

        # Check that a new conversation was created and added to the DB
        assert mock_db_session.add.call_count == 2  # Once for Conversation, once for Message
        
        # Verify the first object added was a Conversation instance
        new_conversation_instance = mock_db_session.add.call_args_list[0].args[0]
        assert isinstance(new_conversation_instance, Conversation)
        assert new_conversation_instance.user_id == user_id
        assert new_conversation_instance.entry_date == entry_date
        assert new_conversation_instance.status == ConversationStatus.active
        
        # Check that the session was committed and the instance refreshed
        assert mock_db_session.commit.call_count == 2
        assert mock_db_session.refresh.call_count == 2

        # Check the returned objects
        assert conversation is not None
        assert initial_message is not None
        assert initial_message.role == MessageRole.ai

async def test_start_conversation_returns_existing_if_active(
    conversation_service: ConversationService,
    mock_db_session: AsyncMock
):
    """
    Test that an existing active conversation is returned if one is found.
    """
    user_id = 1
    entry_date = date(2023, 1, 16)
    
    # 1. Setup: Simulate an existing conversation and its first message in the DB
    existing_convo = Conversation(
        id=101, 
        user_id=user_id, 
        entry_date=entry_date, 
        status=ConversationStatus.active
    )
    first_message = Message(
        id=202,
        conversation_id=existing_convo.id,
        role=MessageRole.ai,
        content="Welcome back!"
    )

    # 2. Patch the service method to simulate finding an active conversation
    with patch.object(conversation_service, 'get_active_conversation', new_callable=AsyncMock) as mock_get_active:
        mock_get_active.return_value = existing_convo

        # The subsequent query for the first message should return our mock message
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = first_message
        mock_db_session.execute.return_value = mock_result

        # 3. Action: Call the service method
        conversation, message = await conversation_service.start_conversation(
            user_id=user_id,
            entry_date=entry_date,
            timezone="UTC"
        )

        # 4. Assertions
        # Check that the returned objects are the ones we mocked
        assert conversation.id == existing_convo.id
        assert message.id == first_message.id
        
        # Crucially, ensure no new objects were added or committed
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
        mock_db_session.refresh.assert_not_called()

        # Ensure get_active_conversation and the subsequent db.execute were called
        mock_get_active.assert_awaited_once_with(user_id, entry_date)
        mock_db_session.execute.assert_awaited_once()

async def test_start_conversation_forces_new_if_active_exists(
    conversation_service: ConversationService,
    mock_db_session: AsyncMock
):
    """
    Test that a new conversation is created when force_new=True,
    and the existing active conversation is completed.
    """
    user_id = 1
    entry_date = date(2023, 1, 17)
    
    # 1. Setup: Simulate an existing active conversation
    existing_convo = Conversation(
        id=102, 
        user_id=user_id, 
        entry_date=entry_date, 
        status=ConversationStatus.active
    )

    # 2. Patch the service method to simulate finding this active conversation
    with patch.object(conversation_service, 'get_active_conversation', new_callable=AsyncMock) as mock_get_active:
        mock_get_active.return_value = existing_convo

        # 3. Action: Call the service method with force_new=True
        new_conversation, new_initial_message = await conversation_service.start_conversation(
            user_id=user_id,
            entry_date=entry_date,
            timezone="UTC",
            force_new=True
        )

        # 4. Assertions
        mock_get_active.assert_awaited_once_with(user_id, entry_date)
        
        # Check that the existing conversation was marked as completed
        assert existing_convo.status == ConversationStatus.completed
        assert existing_convo.ended_at is not None
        
        # Check that the change was committed
        # It should be called once for completing the old, and twice for the new convo/message
        assert mock_db_session.commit.call_count == 3

        # Check that a NEW conversation was created
        assert new_conversation is not None
        assert new_conversation.id != existing_convo.id
        
        # Check that new objects (conversation and message) were added to the session
        assert mock_db_session.add.call_count == 2
        new_convo_instance = mock_db_session.add.call_args_list[0].args[0]
        assert isinstance(new_convo_instance, Conversation)
        assert new_convo_instance.user_id == user_id
        assert new_convo_instance.status == ConversationStatus.active