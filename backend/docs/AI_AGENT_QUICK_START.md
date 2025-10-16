# Quick Start: Building the AI Agent Foundation

**Estimated Time**: 1-2 weeks  
**Goal**: Implement Phase 1 - Agent Foundation with Orchestrator, Context Manager, and Conversation Memory

---

## Step 1: Create Agent Orchestrator (`backend/src/core/agent.py`)

This is the central intelligence hub that coordinates all AI decisions.

```python
"""
Core AI Agent Orchestrator for centralized financial decision-making
"""

from typing import Dict, Any, Optional, List
from uuid import uuid4
from sqlalchemy.orm import Session
from src.models.expense import Expense
from src.services.categorization_service import CategorizationService
from src.services.ocr_service import OCRService
from src.services.budget_management_service import BudgetManagementService


class AgentDecision:
    """Represents a decision made by the agent"""
    
    def __init__(
        self,
        category: Optional[str],
        confidence: float,
        action: str,  # 'auto_categorize', 'suggest', 'ask_user', 'alert'
        reasoning: str,
        alternative_categories: Optional[List[str]] = None,
    ):
        self.category = category
        self.confidence = confidence
        self.action = action
        self.reasoning = reasoning
        self.alternative_categories = alternative_categories or []
        self.decision_id = str(uuid4())
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'category': self.category,
            'confidence': self.confidence,
            'action': self.action,
            'reasoning': self.reasoning,
            'alternative_categories': self.alternative_categories,
        }


class FinancialAgent:
    """
    Central AI Agent for autonomous financial decision-making.
    Coordinates categorization, budgeting, and financial advice.
    """
    
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        self.categorization_service = CategorizationService()
        self.budget_service = BudgetManagementService()
        
    def process_expense(
        self, 
        expense: Expense,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> AgentDecision:
        """
        Process an expense with intelligent decision-making.
        
        Decision hierarchy:
        1. Check user preference overrides
        2. Get AI categorization
        3. Check for anomalies
        4. Apply confidence thresholds
        5. Return decision with action
        """
        
        # 1. Check user preferences if provided
        if user_preferences:
            preferred_category = self._check_user_preferences(expense, user_preferences)
            if preferred_category:
                return AgentDecision(
                    category=preferred_category['category'],
                    confidence=0.95,
                    action='auto_categorize',
                    reasoning=f"Matched user preference: {preferred_category['reason']}"
                )
        
        # 2. Get AI suggestion
        ai_suggestion = self.categorization_service.suggest_category(
            self.user_id, 
            expense.id, 
            self.db
        )
        
        # 3. Apply decision logic
        if ai_suggestion['confidence'] >= 0.9:
            return AgentDecision(
                category=ai_suggestion['suggested_category_name'],
                confidence=ai_suggestion['confidence'],
                action='auto_categorize',
                reasoning=ai_suggestion['reason']
            )
        elif ai_suggestion['confidence'] >= 0.7:
            return AgentDecision(
                category=ai_suggestion['suggested_category_name'],
                confidence=ai_suggestion['confidence'],
                action='suggest',
                reasoning=ai_suggestion['reason'],
                alternative_categories=['Other', 'Uncategorized']
            )
        else:
            return AgentDecision(
                category=ai_suggestion['suggested_category_name'],
                confidence=ai_suggestion['confidence'],
                action='ask_user',
                reasoning="Low confidence - requesting user confirmation"
            )
    
    def _check_user_preferences(
        self, 
        expense: Expense, 
        preferences: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if expense matches user preferences"""
        # TODO: Implement user preference matching logic
        # This will check spending patterns and user history
        return None
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and recommendations"""
        # TODO: Analyze budget vs spending
        # TODO: Generate recommendations
        return {}
    
    def get_financial_insights(self, period: str = 'monthly') -> Dict[str, Any]:
        """Generate financial insights for user"""
        # TODO: Combine multiple data sources
        # TODO: Generate personalized insights
        return {}


__all__ = ['FinancialAgent', 'AgentDecision']
```

---

## Step 2: Create User Context Manager (`backend/src/services/user_context_service.py`)

This stores and retrieves user preferences and patterns.

```python
"""
User Context Service for maintaining user preferences and spending patterns
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from src.models.category import Category
from src.models.expense import Expense
from src.models.budget import Budget
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class UserContextService:
    """Manages user context including preferences, goals, and spending patterns"""
    
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        self._context_cache = None
        
    def get_context(self) -> 'UserContext':
        """Get user context (with caching)"""
        if self._context_cache is None:
            self._context_cache = self._load_context()
        return self._context_cache
    
    def _load_context(self) -> 'UserContext':
        """Load user context from database"""
        
        # Get user categories
        categories = self.db.query(Category).filter(
            Category.user_id == self.user_id
        ).all()
        
        # Get spending patterns (last 3 months)
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        recent_expenses = self.db.query(Expense).filter(
            Expense.user_id == self.user_id,
            Expense.date >= three_months_ago
        ).all()
        
        # Get user budgets
        budgets = self.db.query(Budget).filter(
            Budget.user_id == self.user_id
        ).all()
        
        return UserContext(
            user_id=self.user_id,
            categories=categories,
            recent_expenses=recent_expenses,
            budgets=budgets
        )
    
    def refresh_context(self):
        """Force refresh of cached context"""
        self._context_cache = None


class UserContext:
    """Represents user's financial context"""
    
    def __init__(
        self,
        user_id: str,
        categories: List[Any],
        recent_expenses: List[Any],
        budgets: List[Any]
    ):
        self.user_id = user_id
        self.categories = categories
        self.recent_expenses = recent_expenses
        self.budgets = budgets
        self._patterns = self._compute_patterns()
    
    def _compute_patterns(self) -> Dict[str, Any]:
        """Compute spending patterns from recent expenses"""
        patterns = {
            'by_category': {},
            'by_merchant': {},
            'avg_transaction': 0,
        }
        
        if not self.recent_expenses:
            return patterns
        
        # Compute category totals
        total = 0
        for expense in self.recent_expenses:
            category = expense.category or 'Uncategorized'
            if category not in patterns['by_category']:
                patterns['by_category'][category] = {
                    'total': 0,
                    'count': 0,
                    'avg': 0,
                }
            patterns['by_category'][category]['total'] += expense.amount
            patterns['by_category'][category]['count'] += 1
            total += expense.amount
        
        # Compute averages
        if self.recent_expenses:
            patterns['avg_transaction'] = total / len(self.recent_expenses)
        
        for category in patterns['by_category']:
            stats = patterns['by_category'][category]
            stats['avg'] = stats['total'] / stats['count'] if stats['count'] > 0 else 0
        
        return patterns
    
    def get_category_average(self, category: str) -> float:
        """Get average spending for a category"""
        if category in self._patterns['by_category']:
            return self._patterns['by_category'][category]['avg']
        return 0
    
    def get_all_patterns(self) -> Dict[str, Any]:
        """Get all spending patterns"""
        return self._patterns


__all__ = ['UserContextService', 'UserContext']
```

---

## Step 3: Create Conversation History Model (`backend/src/models/conversation.py`)

```python
"""
Conversation History model for multi-turn AI interactions
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.core.database import Base


class AIConversation(Base):
    """Stores conversation history for multi-turn dialogs with AI"""
    
    __tablename__ = "ai_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    user_input = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    user_feedback = Column(Boolean, nullable=True)  # True if user accepted, False if rejected, None if no feedback
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'conversation_id': str(self.conversation_id),
            'turn_number': self.turn_number,
            'user_input': self.user_input,
            'agent_response': self.agent_response,
            'reasoning': self.reasoning,
            'user_feedback': self.user_feedback,
            'created_at': self.created_at.isoformat(),
        }


__all__ = ['AIConversation']
```

---

## Step 4: Add Database Migration

Create file: `backend/migrations/add_conversation_history.sql`

```sql
-- Create conversations table
CREATE TABLE IF NOT EXISTS ai_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    turn_number INTEGER NOT NULL,
    user_input TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    reasoning TEXT,
    user_feedback BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_ai_conversations_user_id ON ai_conversations(user_id);
CREATE INDEX idx_ai_conversations_conversation_id ON ai_conversations(conversation_id);
CREATE INDEX idx_ai_conversations_created_at ON ai_conversations(created_at);
```

**Run migration**:
```bash
cd backend
supabase migration up
# OR manually execute SQL in Supabase
```

---

## Step 5: Update Categorization Service to Use Agent

Modify: `backend/src/services/categorization_service.py`

```python
# At the top of the file, add:
from src.core.agent import FinancialAgent

# In the suggest_category method, add agent decision logic:
def suggest_category_with_agent(
    self, 
    user_id: str, 
    expense_id: str, 
    db_session: Session = None,
    user_preferences: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Suggest category using AI Agent for intelligent decision-making
    """
    if not db_session:
        return self.suggest_category(user_id, expense_id, db_session)
    
    # Get expense
    expense = db_session.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise CategorizationServiceError(f"Expense {expense_id} not found")
    
    # Use agent for decision
    agent = FinancialAgent(user_id, db_session)
    decision = agent.process_expense(expense, user_preferences)
    
    return {
        'suggested_category_name': decision.category,
        'confidence_score': decision.confidence,
        'action': decision.action,
        'reasoning': decision.reasoning,
        'decision_id': decision.decision_id,
        'alternatives': decision.alternative_categories,
    }
```

---

## Step 6: Add New API Endpoint for Agent

Create: `backend/src/api/v1/agent_router.py`

```python
"""
AI Agent API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from src.core.database import get_db
from src.core.security import get_current_user
from src.core.agent import FinancialAgent
from src.models.user import User
from src.models.conversation import AIConversation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["ai-agent"])


@router.get("/conversation-history")
async def get_conversation_history(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation history for current user"""
    try:
        conversations = db.query(AIConversation).filter(
            AIConversation.user_id == current_user.id
        ).order_by(AIConversation.created_at.desc()).limit(limit).all()
        
        return {
            'conversations': [c.to_dict() for c in conversations],
            'total': len(conversations)
        }
    except Exception as e:
        logger.error(f"Error fetching conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching history")


@router.get("/context")
async def get_user_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user context (spending patterns, categories, etc.)"""
    try:
        from src.services.user_context_service import UserContextService
        
        context_service = UserContextService(current_user.id, db)
        context = context_service.get_context()
        
        return {
            'user_id': str(current_user.id),
            'patterns': context.get_all_patterns(),
            'categories': [
                {'id': str(c.id), 'name': c.name} 
                for c in context.categories
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching context: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching context")


@router.get("/status")
async def get_agent_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get agent status and capabilities"""
    return {
        'status': 'active',
        'version': '1.0.0',
        'capabilities': [
            'expense_categorization',
            'budget_optimization',
            'financial_advice',
            'anomaly_detection',
        ],
        'user_id': str(current_user.id),
    }
```

---

## Step 7: Update Main Router

Modify: `backend/src/api/v1/router.py`

```python
# Add at the top
from .agent_router import router as agent_router

# Add before the last line
router.include_router(agent_router, prefix="", tags=["ai-agent"])
```

---

## Step 8: Write Tests

Create: `backend/tests/unit/test_agent.py`

```python
"""
Tests for AI Agent core functionality
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from src.core.agent import FinancialAgent, AgentDecision
from src.models.expense import Expense


@pytest.fixture
def agent():
    mock_db = MagicMock()
    agent = FinancialAgent(str(uuid4()), mock_db)
    return agent


def test_agent_decision_creation():
    """Test creating an agent decision"""
    decision = AgentDecision(
        category='Dining',
        confidence=0.95,
        action='auto_categorize',
        reasoning='High confidence match'
    )
    
    assert decision.category == 'Dining'
    assert decision.confidence == 0.95
    assert decision.action == 'auto_categorize'
    assert decision.decision_id is not None


def test_agent_decision_to_dict():
    """Test converting decision to dict"""
    decision = AgentDecision(
        category='Dining',
        confidence=0.85,
        action='suggest',
        reasoning='Moderate confidence',
        alternative_categories=['Food', 'Entertainment']
    )
    
    decision_dict = decision.to_dict()
    assert decision_dict['category'] == 'Dining'
    assert decision_dict['confidence'] == 0.85
    assert 'decision_id' in decision_dict
    assert len(decision_dict['alternative_categories']) == 2


def test_agent_initialization():
    """Test agent initialization"""
    mock_db = MagicMock()
    user_id = str(uuid4())
    agent = FinancialAgent(user_id, mock_db)
    
    assert agent.user_id == user_id
    assert agent.db is not None
```

---

## Step 9: Update requirements.txt

Add new dependencies if needed:

```
# Existing dependencies remain...

# For agent context management
redis>=4.5.0  # Optional: for caching user context
numpy>=1.24.0  # For pattern analysis
pandas>=2.0.0  # For spending pattern calculation
```

---

## Verification Checklist

- [ ] Created `backend/src/core/agent.py` with `FinancialAgent` class
- [ ] Created `backend/src/services/user_context_service.py`
- [ ] Created `backend/src/models/conversation.py`
- [ ] Added database migration for `ai_conversations` table
- [ ] Updated `backend/src/services/categorization_service.py` to use agent
- [ ] Created `backend/src/api/v1/agent_router.py` with new endpoints
- [ ] Updated `backend/src/api/v1/router.py` to include agent routes
- [ ] Created `backend/tests/unit/test_agent.py` with tests
- [ ] Ran migration successfully
- [ ] Tests pass: `pytest backend/tests/unit/test_agent.py`
- [ ] API endpoints accessible: `GET /api/v1/agent/status`

---

## Next Steps (Phase 2)

Once Phase 1 is complete:

1. **Add Anomaly Detection** (`anomaly_detection_service.py`)
2. **Implement Smart Categorization Rules** (decision tree)
3. **Add Goal Tracking** (`financial_goal` model + service)
4. **Multi-Turn Conversations** (conversation management)

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Database migration fails | Check Supabase connection; ensure UUID extension enabled |
| Agent not making decisions | Verify `categorization_service` is being called correctly |
| API returns 500 error | Check logs with `mcp_supabase_get_logs` |
| Tests failing | Ensure all mocks are properly configured |

---

**For more details, see:**
- Full Analysis: `backend/docs/AI_AGENT_ANALYSIS.md`
- Vietnamese Guide: `backend/docs/PHAN_TICH_AI_AGENT_VN.md`
