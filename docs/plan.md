# LLM-Assisted Work Management System - Updated Plan

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
OpenWebUI + LiteLLM ↔ FastAPI Server (Knowledge System) ↔ PostgreSQL + pgvector
    ↑ (Chat Interface)     ↑ (OpenAPI Tools)                    ↑ (Hybrid Search)
                         Redis (Caching)
```

### Technology Stack (Finalized)
#### Backend Layer  
- **API Framework**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+ with pgvector extension (pgvector/pgvector:pg15)
- **Vector Storage**: pgvector extension for 1536-dimension embeddings
- **Search**: PostgreSQL full-text search + vector similarity (hybrid)
- **Caching**: Redis 7 for session and query caching
- **Embeddings**: OpenAI text-embedding-3-small
- **Entity Extraction**: Anthropic Claude for intelligent entity recognition

#### LLM Integration
- **Chat Interface**: OpenWebUI (already running on port 3000)
- **Model Proxy**: LiteLLM (already running on port 4000)
- **Tool Integration**: FastAPI OpenAPI spec consumed by OpenWebUI

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

#### OpenWebUI + LiteLLM
- **Chat interface** for natural language interaction
- **Tool discovery** and execution via OpenAPI
- **Multi-model support** through LiteLLM proxy

## Implementation Status

### ✅ Phase 1: Core Infrastructure (COMPLETE)
**Delivered:**
- ✅ Development environment with Docker Compose
- ✅ PostgreSQL 15 with pgvector extension
- ✅ Complete database schema with vector support
- ✅ FastAPI application with health checks
- ✅ Development scripts for setup, testing, and management
- ✅ Proper logging and error handling

### ✅ Phase 2: Note Management Core (COMPLETE)
**Delivered:**
- ✅ **Complete Note Storage Pipeline**: Text → Entity Extraction → Embedding → Database (4.2s processing)
- ✅ **Advanced Entity Extraction**: Claude-powered extraction with high confidence scores (0.85-0.95)
- ✅ **Hybrid Search Engine**: PostgreSQL full-text + pgvector semantic similarity with relevance ranking
- ✅ **Robust API Layer**: FastAPI with proper Pydantic models and OpenAPI documentation
- ✅ **Data Model Alignment**: Clean mapping between database schema and API responses
- ✅ **OpenAI Integration**: 1536-dimension embeddings with pgvector storage
- ✅ **Entity Registry**: Deduplication and relationship tracking
- ✅ **Type-Safe Models**: Pydantic validation throughout

**Technical Achievements:**
- OpenAI embeddings generation and storage
- Entity extraction using Anthropic Claude
- Hybrid search with relevance scoring
- Database connection pooling with asyncpg
- Hot-reload development environment
- Comprehensive error handling and logging

**Test Results (Verified Working):**
```bash
# Health check - ✅ PASS
curl http://localhost:8000/health
{"success":true,"message":"Health check completed in 35ms","services":{"postgresql":"healthy","pgvector":"healthy"},"version":"1.0.0"}

# Note storage - ✅ PASS (4.2s processing, 4 entities extracted)
curl -X POST "http://localhost:8000/tools/notes" -H "Content-Type: application/json" -d '{"text": "Had a meeting with John about ProjectX. We discussed the new React components and decided to use TypeScript."}'

# Search - ✅ PASS (1.16s query time, 3 results with relevance ranking)
curl "http://localhost:8000/tools/notes/search?query=John%20ProjectX&limit=5"

# Entity filtering - ✅ PASS (fixed parameter binding issue)
curl "http://localhost:8000/tools/notes/search?query=React&entity_filter=John"
```

### 🧪 Phase 2.5: Testing & Validation (CURRENT - 1-2 weeks)
**Current Priority:** Comprehensive testing framework for production readiness.

**Tasks in Progress:**
- [ ] Docker-based pytest setup
- [ ] Integration tests for complete workflows
- [ ] Service layer unit tests
- [ ] Performance benchmarks
- [ ] Error handling validation
- [ ] Test coverage reporting

### 🚀 Phase 3: Advanced Search & Analytics (3-4 weeks)
**Deliverables:**
- Enhanced semantic search with faceted filtering
- Entity relationship analysis and visualization
- Topic clustering and trend analysis
- Search analytics and user behavior tracking
- Performance optimization and Redis caching

**Tasks:**
1. Implement advanced search filters (date ranges, entity types, confidence thresholds)
2. Build entity relationship mapping and graph analysis
3. Create topic clustering using embeddings
4. Add search result ranking improvements
5. Implement Redis caching layer for frequent queries
6. Add search analytics and metrics collection

### 🚀 Phase 4: Planning & Workflow Intelligence (3-4 weeks)
**Deliverables:**
- Weekly summary generation with LLM insights
- Action item extraction and status tracking
- Temporal intention detection and planning
- Project momentum analysis
- Deadline and dependency management

**Tasks:**
1. Implement weekly summary generation using LLM
2. Build action item extraction from notes
3. Create temporal intention detection (dates, deadlines)
4. Develop weekly planning algorithm with historical context
5. Add project tracking and momentum analysis
6. Integrate planning session management

### 🎯 Phase 5: Tool Integration (3-5 days) - REVISED
**Deliverables:**
- OpenWebUI tool registration and testing
- Enhanced OpenAPI specifications for LLM clarity
- End-to-end workflow validation
- User documentation and examples

**Tasks:**
1. Register API server as tool in OpenWebUI (30 minutes)
2. Enhance OpenAPI descriptions for better LLM understanding (2-3 hours)
3. Test tool discovery and execution with multiple models (1-2 days)
4. Create usage examples and documentation (1 day)
5. Debug and polish tool integration (1 day)

**Note:** OpenWebUI and LiteLLM already running - this phase is primarily configuration and testing.

### 🚀 Phase 6: Production Deployment & Polish (2-3 weeks)
**Deliverables:**
- Production Docker Compose with security hardening
- Monitoring, logging, and alerting infrastructure
- User authentication and multi-tenancy support
- Backup and disaster recovery procedures
- Performance monitoring and optimization

**Tasks:**
1. Create production deployment configuration
2. Implement user authentication and session management
3. Add monitoring with Prometheus/Grafana
4. Set up automated backups and recovery
5. Load testing and performance optimization
6. Security audit and hardening

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
    embedding vector(1536) NULL,
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

## API Specification (Implemented)

### Current Tool Endpoints
```python
# Health and system endpoints
@app.get("/health")
async def health_check() -> HealthResponse

@app.get("/")
async def root()

# Tool endpoints for LLM integration
@app.post("/tools/notes", response_model=StoreNoteResponse)
async def store_note_tool(request: StoreNoteRequest) -> StoreNoteResponse

@app.get("/tools/notes/search", response_model=SearchNotesResponse)
async def search_notes_tool(
    query: str,
    limit: int = 10,
    days_back: Optional[int] = 30,
    entity_filter: Optional[str] = None
) -> SearchNotesResponse
```

### Pydantic Models (Implemented)
```python
class StoreNoteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(default=[])
    session_id: Optional[str] = Field(None)

class StoreNoteResponse(BaseResponse):
    note_id: str
    entities: List[Dict[str, Any]]
    processing_time_ms: int = 0
    embedding_dimensions: int = 0

class SearchNotesResponse(BaseResponse):
    results: List[NoteSearchResult]
    metadata: SearchMetadata

class NoteSearchResult(BaseModel):
    id: str
    text: str
    timestamp: datetime
    extracted_entities: List[EntityMention]
    linked_entities: List[EntityMention]
    relevance_score: float
    similarity_score: Optional[float]
    text_rank: Optional[float]
```

## Current File Structure

```
work-management-system/
├── docker-compose.dev.yml     # Development environment (updated with test service)
├── .env.dev                   # Development environment variables
├── Dockerfile                 # FastAPI application container
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies (includes pytest)
├── database/
│   ├── init.sql              # Complete database schema with pgvector
│   ├── migrations/           # Future schema changes
│   └── seeds/                # Test data
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application with working tool endpoints
│   ├── config.py            # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   └── dbconfig.py      # Database manager with pgvector support
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py          # Base models and utilities
│   │   ├── notes.py         # Note-related models
│   │   └── search.py        # Search-related models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py        # OpenAI embeddings
│   │   ├── anthropic_handler.py     # Custom Anthropic handler
│   │   ├── entity_service.py        # Entity extraction
│   │   ├── note_service.py          # Note orchestration
│   │   └── database_service.py      # Database operations
│   └── middleware/
│       └── __init__.py
├── tests/
│   ├── conftest.py          # Test configuration (to be implemented)
│   ├── test_integration.py  # End-to-end tests (to be implemented)
│   ├── test_services.py     # Service layer tests (to be implemented)
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── scripts/
│   ├── dev-setup.sh        # Complete environment setup
│   ├── dev-test.sh         # Comprehensive testing
│   └── dev-logs.sh         # Log management
└── docs/
    └── plan.md             # This document
```

## Development Environment (Working)

### Docker Compose Configuration
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg15
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
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - dev-backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - dev-backend

  adminer:
    image: adminer
    ports:
      - "8080:8080"
    networks:
      - dev-backend

  # Test service (to be added)
  test:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/work_management_dev
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=testing
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - dev-backend
    profiles:
      - testing
    command: ["python", "-m", "pytest", "/app/tests", "-v"]
```

### Development Workflow (Current)
```bash
# Start development environment
./scripts/dev-setup.sh

# Run tests with Docker
docker-compose -f docker-compose.dev.yml --profile testing run --rm test

# Test API endpoints (all working)
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/tools/notes" -H "Content-Type: application/json" -d '{"text": "Test note"}'
curl "http://localhost:8000/tools/notes/search?query=test&limit=5"

# Access services
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs  
# - Database Admin: http://localhost:8080
# - OpenWebUI: http://localhost:3000 (separate stack)
# - LiteLLM: http://localhost:4000 (separate stack)
```

## Progress Summary

### 📊 Overall Progress: ~40% Complete

**✅ Completed (Phases 1-2):**
- Complete development infrastructure
- Production-ready note storage and search system
- Advanced entity extraction with Claude
- Hybrid search with relevance