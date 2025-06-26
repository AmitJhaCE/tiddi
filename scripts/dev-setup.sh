#!/bin/bash
set -e

echo "🚀 Setting up Work Management System development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Copy .env.example to .env and configure your API keys"
    cp .env.example .env
    echo "✅ Created .env from template"
    echo "⚠️  Please edit .env with your actual API keys before continuing"
    exit 1
fi

# Check if required API keys are set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_key_here" ]; then
    echo "⚠️  Please set OPENAI_API_KEY in .env"
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_key_here" ]; then
    echo "⚠️  Please set ANTHROPIC_API_KEY in .env"
fi

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose -f docker-compose.dev.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# PostgreSQL
if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U postgres; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
    exit 1
fi

# Check pgvector extension
if docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d work_management_dev -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" > /dev/null 2>&1; then
    echo "✅ pgvector extension is available"
else
    echo "❌ pgvector extension is not available"
    exit 1
fi

# Redis
if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# FastAPI
echo "🔍 Checking FastAPI..."
sleep 10  # Give FastAPI more time to start
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI is ready"
    
    # Check health details
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        echo "✅ All services are healthy"
    else
        echo "⚠️  Some services may have issues:"
        echo "$HEALTH_RESPONSE" | jq '.services' 2>/dev/null || echo "$HEALTH_RESPONSE"
    fi
else
    echo "❌ FastAPI is not ready"
    echo "🔍 FastAPI logs:"
    docker-compose -f docker-compose.dev.yml logs --tail=20 api
    exit 1
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Services running:"
echo "   - FastAPI API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo "   - Database Admin: http://localhost:8080"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "   - View API logs: ./scripts/dev-logs.sh api"
echo "   - View all logs: ./scripts/dev-logs.sh"
echo "   - Run tests: ./scripts/dev-test.sh"
echo "   - Database shell: ./scripts/db-shell.sh"
echo "   - Reset environment: ./scripts/dev-reset.sh"
echo "   - Stop services: ./scripts/dev-stop.sh"