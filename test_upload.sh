#!/bin/bash

# Test script for file upload server

echo "🧪 Testing File Upload Server"
echo ""

# Check if server is running
if ! curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "❌ Server is not running on port 8080"
    echo "   Start the server with: ./run.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Create test directory
TEST_DIR="./test_files"
mkdir -p "$TEST_DIR"

# Test 1: Small file (1KB)
echo "Test 1: Small file (1KB)"
echo "This is a small test file" > "$TEST_DIR/small.txt"
curl -X POST -F "file=@$TEST_DIR/small.txt" http://localhost:8080/ 2>/dev/null | jq '.'
echo ""

# Test 2: Medium file (1MB)
echo "Test 2: Medium file (1MB)"
dd if=/dev/zero of="$TEST_DIR/medium.bin" bs=1048576 count=1 2>/dev/null
curl -X POST -F "file=@$TEST_DIR/medium.bin" http://localhost:8080/ 2>/dev/null | jq '.'
echo ""

# Test 3: Duplicate file (should be skipped)
echo "Test 3: Duplicate upload (should be skipped)"
curl -X POST -F "file=@$TEST_DIR/small.txt" http://localhost:8080/ 2>/dev/null | jq '.'
echo ""

# Test 4: Modified file (should create version)
echo "Test 4: Modified file (should create version)"
echo "This is a modified test file" > "$TEST_DIR/small.txt"
curl -X POST -F "file=@$TEST_DIR/small.txt" http://localhost:8080/ 2>/dev/null | jq '.'
echo ""

# Test 5: List files
echo "Test 5: List uploaded files"
curl -s http://localhost:8080/list 2>/dev/null | jq '.'
echo ""

# Cleanup
echo "🧹 Cleaning up test files..."
rm -rf "$TEST_DIR"

echo ""
echo "✅ All tests completed!"
echo ""
echo "Manual test instructions:"
echo "  1. Open http://localhost:8080 in Chrome"
echo "  2. Drag and drop a folder or files"
echo "  3. Watch the upload progress"
echo "  4. Check ./uploads directory for files"
