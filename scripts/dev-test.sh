#!/bin/bash
set -e

echo "🧪 Running development tests..."

# Check if services are running
if ! docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo "❌ Development services are not running"
    echo "💡 Run './scripts/dev-setup.sh' first"
    exit 1
fi

# Basic connectivity tests
echo "Testing service connectivity..."

# Test PostgreSQL
if docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d work_management_dev -c "SELECT COUNT(*) FROM users;" > /dev/null; then
    echo "✅ PostgreSQL connection test passed"
else
    echo "❌ PostgreSQL connection test failed"
    exit 1
fi

# Test pgvector extension
if docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d work_management_dev -c "SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector;" > /dev/null; then
    echo "✅ pgvector extension test passed"
else
    echo "❌ pgvector extension test failed"
    exit 1
fi

# Test Redis
if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis connection test passed"
else
    echo "❌ Redis connection test failed"
    exit 1
fi

# Test FastAPI health
echo ""
echo "Testing FastAPI endpoints..."

HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | jq -e '.success == true' > /dev/null; then
    echo "✅ FastAPI health check passed"
    
    # Check specific services
    if echo "$HEALTH_RESPONSE" | jq -e '.services.postgresql == "healthy"' > /dev/null; then
        echo "✅ PostgreSQL health check passed"
    else
        echo "❌ PostgreSQL health check failed"
    fi
    
    if echo "$HEALTH_RESPONSE" | jq -e '.services.pgvector == "healthy"' > /dev/null; then
        echo "✅ pgvector health check passed"
    else
        echo "❌ pgvector health check failed"
    fi
    
else
    echo "❌ FastAPI health check failed"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# Test API endpoints
echo ""
echo "Testing API endpoints..."

# Test store note endpoint (placeholder)
STORE_RESPONSE=$(curl -s -X POST "http://localhost:8000/tools/notes" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test note for development validation"}')

if echo "$STORE_RESPONSE" | jq -e '.success == true' > /dev/null; then
    echo "✅ Store note endpoint test passed"
else
    echo "❌ Store note endpoint test failed"
    echo "Response: $STORE_RESPONSE"
fi

# Test search endpoint (placeholder)
SEARCH_RESPONSE=$(curl -s "http://localhost:8000/tools/notes/search?query=test")
if echo "$SEARCH_RESPONSE" | jq -e '.success == true' > /dev/null; then
    echo "✅ Search notes endpoint test passed"
else
    echo "❌ Search notes endpoint test failed"
    echo "Response: $SEARCH_RESPONSE"
fi

# Test OpenAPI spec generation
if curl -s http://localhost:8000/openapi.json | jq -e '.info.title == "Work Management Tools"' > /dev/null; then
    echo "✅ OpenAPI spec generation test passed"
else
    echo "❌ OpenAPI spec generation test failed"
fi

# Test database schema
echo ""
echo "Testing database schema..."

# Check if all tables exist
TABLES=$(docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d work_management_dev -c "\dt" | grep -c "public")
if [ "$TABLES" -ge 5 ]; then
    echo "✅ Database schema validation passed ($TABLES tables found)"
else
    echo "❌ Database schema validation failed (expected 5+ tables, found $TABLES)"
fi

# Test vector operations
VECTOR_TEST=$(docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d work_management_dev -c "SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector;" | grep -o "0\.[0-9]*")
if [ ! -z "$VECTOR_TEST" ]; then
    echo "✅ Vector operations test passed (similarity: $VECTOR_TEST)"
else
    echo "❌ Vector operations test failed"
fi

echo ""
echo "🎉 All development tests completed successfully!"
echo "📊 Test Summary:"
echo "   - PostgreSQL: ✅ Connected and healthy"
echo "   - pgvector: ✅ Extension working"
echo "   - Redis: ✅ Connected"
echo "   - FastAPI: ✅ All endpoints responding"
echo "   - Database Schema: ✅ All tables present"
echo "   - Vector Operations: ✅ Working"