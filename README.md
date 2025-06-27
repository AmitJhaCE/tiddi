# tiddi
Tiddi can leverage ai to help manage your work.

## Useful Commands

### Run all tests using the test profile
docker-compose -f docker-compose.dev.yml --profile testing run --rm test

### Alternative: Run all tests with more verbose output
docker-compose -f docker-compose.dev.yml --profile testing run --rm test python -m pytest /app/tests -v --tb=long

### Run only the bulk notes test file
docker-compose -f docker-compose.dev.yml --profile testing run --rm test python -m pytest /app/tests/test_bulk_notes.py -v

### Run specific bulk test methods
docker-compose -f docker-compose.dev.yml --profile testing run --rm test python -m pytest /app/tests/test_bulk_notes.py::TestBulkNotesAPI::test_bulk_store_5_notes -v

### Run all bulk tests with performance timing
docker-compose -f docker-compose.dev.yml --profile testing run --rm test python -m pytest /app/tests/test_bulk_notes.py -v -s --tb=short

### Reset db after tests
docker-compose -f docker-compose.dev.yml --profile db-management run --rm db-reset