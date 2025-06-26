
# LLM-Assisted Work Management System

## Executive Summary
This document specifies the design and implementation of an LLM-assisted work management system for individuals managing multiple projects simultaneously. The system provides a natural API interface with tool endpoints for LLM integration, powered by a robust knowledge management backend that captures, analyzes, and retrieves work activities through semantic search and intelligent planning.

### Core Value Proposition
- **Natural Interface**: RESTful API with OpenAPI specification for LLM tool integration
- **Intelligent Capture**: Automatic entity extraction and semantic indexing of work notes
- **Contextual Search**: Hybrid search combining PostgreSQL full-text and pgvector semantic similarity
- **Cross-Session Continuity**: Context preservation through comprehensive note storage
- **Proactive Planning**: Weekly planning with historical intention surfacing

## System Architecture (Current)

### High-Level Architecture
```
LLM Chat Interface ↔ FastAPI Server (Knowledge System) ↔ PostgreSQL + pgvector
                          ↑ (OpenAPI Tools)                    ↑ (Hybrid Search)
                    Redis (Caching)
```

### Technology Stack (Finalized)
#### Backend Layer  
- **API Framework**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+ with pgvector extension (ankane/pgvector:v0.5.1)
- **Vector Storage**: pgvector extension for 1536-dimension embeddings
- **Search**: PostgreSQL full-text search + vector similarity (hybrid)
- **Caching**: Redis 7 for session and query caching
- **Embeddings**: OpenAI text-embedding-3-small

#### Infrastructure
- **Containerization**: Docker with Docker Compose
- **Development**: Hot-reload, volume mounting, health checks
- **Database Admin**: Adminer web interface

### Component Responsibilities
#### PostgreSQL + pgvector
- **Structured data**: Users, notes, entities, planning sessions, intentions
- **Full-text search**: Built-in PostgreSQL text search with GIN indexes
- **Vector embeddings**: pgvector extension for semantic similarity search
- **Hybrid search**: Combine full-text ranking and cosine similarity scoring

#### FastAPI Server
- **OpenAPI tool endpoints** for LLM integration
- **Entity extraction** and relationship mapping
- **Semantic search** and planning algorithms
- **Health monitoring** and error handling

## Current Implementation Status

### ✅ Phase 1: Complete - Core Infrastructure
**Delivered:**
- ✅ Development environment with Docker Compose
- ✅ PostgreSQL 15 with pgvector extension
- ✅ Complete database schema with vector support
- ✅ FastAPI application with health checks
- ✅ Development scripts for setup, testing, and management
- ✅ Proper logging and error handling

**Current File Structure:**
```
work-management-system/
├── docker-compose.dev.yml     # Development environment
├── .env.dev                   # Development environment variables
├── Dockerfile                 # FastAPI application container
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── database/
│   ├── init.sql              # Complete database schema with pgvector
│   ├── migrations/           # Future schema changes
│   └── seeds/                # Test data
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application with tool endpoints
│   ├── config.py            # Configuration management
│   ├── database/
│   │   └── config.py        # Database manager with pgvector support
│   ├── models/
│   │   └── base.py          # Pydantic models for requests/responses
│   ├── services/            # Business logic (to be implemented)
│   └── middleware/          # Custom middleware
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── scripts/
│   ├── dev-setup.sh        # Complete environment setup
│   ├── dev-test.sh         # Comprehensive testing
│   └── dev-logs.sh         # Log management
└── docs/
    └── plan.md             # This document
```

## Database Schema (Implemented)

**Complete PostgreSQL + pgvector Schema:**
```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Notes with vector embeddings and full-text search
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT,
    text TEXT NOT NULL CHECK (length(text) > 0),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Vector embedding (1536 dimensions for OpenAI)
    embedding vector(1536) NULL,
    
    -- Generated full-text search vector
    text_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    
    extracted_entities JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Entity registry for deduplication
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'project', 'technology', 'concept')),
    aliases JSONB DEFAULT '[]',
    mention_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(canonical_name, entity_type)
);

-- Entity mentions linking
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    mentioned_text TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    position_start INTEGER,
    position_end INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Temporal intentions for planning
CREATE TABLE planned_intentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    intention_text TEXT NOT NULL,
    mentioned_date DATE NOT NULL,
    target_date DATE,
    target_date_fuzzy TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    related_entities JSONB DEFAULT '[]',
    confidence DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Planning sessions
CREATE TABLE planning_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    week_start DATE NOT NULL,
    generated_plan JSONB,
    intentions_surfaced JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_notes_user_timestamp ON notes(user_id, timestamp DESC);
CREATE INDEX idx_notes_text_search ON notes USING gin(text_search_vector);
CREATE INDEX idx_notes_embedding ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_entity_mentions_note_id ON entity_mentions(note_id);
CREATE INDEX idx_entity_mentions_entity_id ON entity_mentions(entity_id);
CREATE INDEX idx_entities_type_name ON entities(entity_type, canonical_name);
CREATE INDEX idx_entities_mention_count ON entities(mention_count DESC);
CREATE INDEX idx_planned_intentions_user_date ON planned_intentions(user_id, target_date);
CREATE INDEX idx_planned_intentions_status ON planned_intentions(status) WHERE status = 'pending';
CREATE INDEX idx_planning_sessions_user_week ON planning_sessions(user_id, week_start);
```

## API Specification (Tool-Ready)

### Current Tool Endpoints (Implemented as Placeholders)
```python
# Health and system endpoints
@app.get("/health")
async def health_check() -> HealthResponse

@app.get("/")
async def root()

# Tool endpoints for LLM integration
@app.post("/tools/notes")
async def store_note_tool(request: StoreNoteRequest) -> StoreNoteResponse

@app.get("/tools/notes/search")
async def search_notes_tool(
    query: str,
    limit: int = 10,
    days_back: Optional[int] = 30,
    entity_filter: Optional[str] = None
) -> SearchNotesResponse
```

### Pydantic Models (Implemented)
```python
class HealthResponse(BaseModel):
    success: bool = True
    message: str
    timestamp: datetime
    services: Dict[str, str]
    version: str = "1.0.0"

class StoreNoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(default=[])
    session_id: Optional[str] = Field(None)

class StoreNoteResponse(BaseModel):
    note_id: str
    entities: List[Dict[str, Any]]
    timestamp: datetime
    success: bool = True
    message: str

class SearchNotesResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query_time_ms: int
    success: bool = True
    message: str
```

## Development Environment (Working)

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  # PostgreSQL with pgvector
  postgres:
    image: ankane/pgvector:v0.5.1
    environment:
      POSTGRES_DB: work_management_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: devpassword
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
    networks:
      - dev-backend

  # FastAPI Development Server
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/work_management_dev
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=DEBUG
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
      - ./database:/app/database
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - dev-backend

  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - dev-backend

  # Database management
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    networks:
      - dev-backend
```

### Environment Configuration
```bash
# .env.dev (Working Configuration)
POSTGRES_PASSWORD=devpassword
POSTGRES_DB=work_management_dev
POSTGRES_USER=postgres
DATABASE_URL=postgresql://postgres:devpassword@localhost:5432/work_management_dev

OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

LOG_LEVEL=DEBUG
ENVIRONMENT=development
MAX_NOTE_LENGTH=10000
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

## Updated Implementation Plan

### ✅ Phase 1: Core Infrastructure (COMPLETE)
**Status: DELIVERED**
- ✅ Development environment with Docker Compose
- ✅ PostgreSQL 15 with pgvector extension
- ✅ Complete database schema with all tables and indexes
- ✅ FastAPI application with health checks and placeholder endpoints
- ✅ Development scripts for setup, testing, and management
- ✅ Comprehensive logging and error handling

### 🚀 Phase 2: Note Management Core (NEXT - 2-3 weeks)
**Deliverables:**
- Note storage with entity extraction using LLM
- OpenAI embedding generation and storage
- Hybrid search (full-text + semantic)
- Entity registry and deduplication
- Real tool endpoint implementation

**Tasks:**
1. Implement OpenAI client for embedding generation
2. Build entity extraction service using Anthropic/OpenAI
3. Create note storage service with embedding processing
4. Implement hybrid search combining text and vector results
5. Build entity registry with deduplication logic
6. Replace placeholder endpoints with real implementations

### Phase 3: Advanced Search and Analysis (2-3 weeks)
**Deliverables:**
- Advanced semantic search with filtering
- Entity relationship analysis
- Topic context analysis
- Performance optimization

**Tasks:**
1. Enhance search with entity filtering and date ranges
2. Implement entity relationship mapping
3. Build topic context analysis with timeline
4. Create dependency analysis for entities
5. Optimize database queries and search performance
6. Add Redis caching layer

### Phase 4: Planning and Workflow (3-4 weeks)
**Deliverables:**
- Weekly summary generation
- Action item extraction and tracking
- Temporal intention processing
- Weekly plan generation

**Tasks:**
1. Implement weekly summary generation with LLM
2. Build action item extraction and status tracking
3. Create temporal intention detection and processing
4. Develop weekly planning algorithm with historical context
5. Add planning session tracking and analytics
6. Integrate all planning tools

### Phase 5: LLM Integration and Chat Interface (2-3 weeks)
**Deliverables:**
- LiteLLM proxy integration
- Open WebUI setup
- End-to-end tool testing
- User authentication

**Tasks:**
1. Add LiteLLM proxy to Docker Compose
2. Set up Open WebUI with tool integration
3. Test tool discovery and execution
4. Implement user identification and session management
5. Add request validation and security middleware
6. Document tool setup and usage

### Phase 6: Testing and Production (2-3 weeks)
**Deliverables:**
- Comprehensive test suite
- Production deployment configuration
- Monitoring and alerting
- Documentation and user guides

**Tasks:**
1. Write unit tests for all services and endpoints
2. Create integration tests for tool workflows
3. Build production Docker Compose with security
4. Implement monitoring, logging, and alerting
5. Create user documentation and setup guides
6. Performance testing and optimization

## Development Workflow (Current)

### Quick Start (Working)
```bash
# 1. Setup environment
cp .env.dev.example .env.dev
# Edit .env.dev with your API keys

# 2. Start development environment
./scripts/dev-setup.sh

# 3. Run tests
./scripts/dev-test.sh

# 4. Access services
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
# - Database Admin: http://localhost:8080
```

### Development Commands
```bash
# View logs
./scripts/dev-logs.sh api

# Test API endpoints
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/tools/notes" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test note"}'

# Database operations
docker-compose -f docker-compose.dev.yml exec postgres \
  psql -U postgres -d work_management_dev

# Test vector operations
docker-compose -f docker-compose.dev.yml exec postgres \
  psql -U postgres -d work_management_dev \
  -c "SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector;"
```

### Current Capabilities
✅ **Working Infrastructure**
- PostgreSQL with pgvector for vector storage
- FastAPI with OpenAPI spec generation
- Health checks for all services
- Development scripts and automation
- Vector similarity operations

✅ **Ready for Phase 2**
- Database schema supports all planned features
- API structure ready for real implementations
- Development environment fully operational
- Vector search foundation in place

## Next Steps: Phase 2 Implementation

### Immediate Priorities
1. **OpenAI Integration** - Implement embedding generation
2. **Entity Extraction** - Use LLM to identify people, projects, concepts
3. **Note Storage** - Store notes with embeddings and extracted entities
4. **Hybrid Search** - Combine PostgreSQL full-text and vector similarity
5. **Tool Implementation** - Replace placeholder endpoints with real functionality

### Success Criteria for Phase 2
- Store notes with automatic entity extraction
- Generate and store OpenAI embeddings
- Perform hybrid search returning ranked results
- Extract and deduplicate entities across notes
- Maintain entity mention relationships

**Current Status: Phase 1 Complete ✅ - Ready for Phase 2 🚀**