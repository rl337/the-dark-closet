#!/bin/bash

# run_checks.sh - Comprehensive validation script for The Dark Closet project
# This script runs all automated tests, static checks, style linting, and coverage

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in a Docker container
check_docker() {
    if [ -f /.dockerenv ]; then
        print_status "Running inside Docker container"
        return 0
    else
        print_warning "Not running in Docker container. Consider using: docker run -v \$(pwd):/app -w /app <image> ./run_checks.sh"
        return 1
    fi
}

# Function to create necessary directories
setup_directories() {
    print_status "Setting up build directories..."
    mkdir -p build/reports
    mkdir -p build/test_outputs
    mkdir -p build/visual_baselines
    mkdir -p build/visual_current
    mkdir -p build/visual_diffs
}

# Function to run code formatting check
run_black_check() {
    print_status "Running Black code formatting check..."
    poetry run black --check --diff .
    print_success "Black formatting check passed"
}

# Function to run code formatting
run_black_format() {
    print_status "Running Black code formatting..."
    poetry run black .
    print_success "Black formatting completed"
}

# Function to run Ruff linting
run_ruff_check() {
    print_status "Running Ruff linting..."
    poetry run ruff check .
    print_success "Ruff linting passed"
}

# Function to run Ruff formatting
run_ruff_format() {
    print_status "Running Ruff formatting..."
    poetry run ruff format .
    print_success "Ruff formatting completed"
}

# Function to run Pylint
run_pylint() {
    print_status "Running Pylint static analysis..."
    poetry run pylint src/ tests/ --output-format=text
    print_success "Pylint analysis passed"
}

# Function to run MyPy type checking
run_mypy() {
    print_status "Running MyPy type checking..."
    poetry run mypy src/
    print_success "MyPy type checking passed"
}

# Function to run all tests
run_tests() {
    print_status "Running all tests..."
    # Skip performance tests in CI environments as they can be flaky due to timing
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
        print_status "Skipping performance tests in CI environment"
        poetry run pytest tests/ \
            --verbose \
            --tb=short \
            --strict-markers \
            --disable-warnings \
            --html=build/reports/pytest_report.html \
            --self-contained-html \
            --cov=src \
            --cov-report=html:build/reports/coverage \
            --cov-report=term-missing \
            --cov-report=xml:build/reports/coverage.xml \
            --junitxml=build/reports/junit.xml \
            -m "not performance"
    else
        poetry run pytest tests/ \
            --verbose \
            --tb=short \
            --strict-markers \
            --disable-warnings \
            --html=build/reports/pytest_report.html \
            --self-contained-html \
            --cov=src \
            --cov-report=html:build/reports/coverage \
            --cov-report=term-missing \
            --cov-report=xml:build/reports/coverage.xml \
            --junitxml=build/reports/junit.xml
    fi
    print_success "All tests passed"
}

# Function to run unit tests only
run_unit_tests() {
    print_status "Running unit tests..."
    # Skip performance tests in CI environments as they can be flaky due to timing
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
        print_status "Skipping performance tests in CI environment"
        poetry run pytest tests/unit/ \
            --verbose \
            --tb=short \
            --strict-markers \
            --disable-warnings \
            --cov=src \
            --cov-report=term-missing \
            -m "not performance"
    else
        poetry run pytest tests/unit/ \
            --verbose \
            --tb=short \
            --strict-markers \
            --disable-warnings \
            --cov=src \
            --cov-report=term-missing
    fi
    print_success "Unit tests passed"
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    poetry run pytest tests/integration/ \
        --verbose \
        --tb=short \
        --strict-markers \
        --disable-warnings
    print_success "Integration tests passed"
}

# Function to run visual tests
run_visual_tests() {
    print_status "Running visual regression tests..."
    # Skip performance tests in CI environments as they can be flaky due to timing
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
        print_status "Skipping performance tests in CI environment"
        poetry run pytest tests/visual/ \
            --verbose \
            --tb=short \
            --strict-markers \
            --disable-warnings \
            -m "not performance"
    else
        poetry run pytest tests/visual/ \
            --verbose \
            --tb=short \
            --strict-markers \
            --disable-warnings
    fi
    print_success "Visual tests passed"
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    poetry run pytest tests/performance/ \
        --verbose \
        --tb=short \
        --strict-markers \
        --disable-warnings
    print_success "Performance tests passed"
}

# Function to check test coverage
check_coverage() {
    print_status "Checking test coverage..."
    poetry run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80
    print_success "Coverage check passed"
}

# Function to run security checks
run_security_checks() {
    print_status "Running security checks..."
    # Check for common security issues
    poetry run ruff check . --select S
    print_success "Security checks passed"
}

# Function to validate project structure
validate_project_structure() {
    print_status "Validating project structure..."
    
    # Check required files exist
    required_files=(
        "pyproject.toml"
        "poetry.lock"
        "pytest.ini"
        "Dockerfile"
        "README.md"
        "AGENTS.md"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    
    # Check required directories exist
    required_dirs=(
        "src/the_dark_closet"
        "tests"
        "tests/unit"
        "tests/integration"
        "tests/visual"
        "tests/performance"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            print_error "Required directory missing: $dir"
            exit 1
        fi
    done
    
    print_success "Project structure validation passed"
}

# Function to clean up build artifacts
cleanup() {
    print_status "Cleaning up build artifacts..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all              Run all checks (default)"
    echo "  --format           Run formatting checks only"
    echo "  --lint             Run linting checks only"
    echo "  --test             Run tests only"
    echo "  --unit             Run unit tests only"
    echo "  --integration      Run integration tests only"
    echo "  --visual           Run visual tests only"
    echo "  --performance      Run performance tests only"
    echo "  --coverage         Run coverage check only"
    echo "  --security         Run security checks only"
    echo "  --structure        Validate project structure only"
    echo "  --clean            Clean up build artifacts"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run all checks"
    echo "  $0 --test          # Run tests only"
    echo "  $0 --format --lint # Run formatting and linting"
}

# Main execution
main() {
    local run_all=true
    local run_format=false
    local run_lint=false
    local run_test=false
    local run_unit=false
    local run_integration=false
    local run_visual=false
    local run_performance=false
    local run_coverage=false
    local run_security=false
    local run_structure=false
    local run_clean=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                run_all=true
                shift
                ;;
            --format)
                run_all=false
                run_format=true
                shift
                ;;
            --lint)
                run_all=false
                run_lint=true
                shift
                ;;
            --test)
                run_all=false
                run_test=true
                shift
                ;;
            --unit)
                run_all=false
                run_unit=true
                shift
                ;;
            --integration)
                run_all=false
                run_integration=true
                shift
                ;;
            --visual)
                run_all=false
                run_visual=true
                shift
                ;;
            --performance)
                run_all=false
                run_performance=true
                shift
                ;;
            --coverage)
                run_all=false
                run_coverage=true
                shift
                ;;
            --security)
                run_all=false
                run_security=true
                shift
                ;;
            --structure)
                run_all=false
                run_structure=true
                shift
                ;;
            --clean)
                run_clean=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Check if we're in Docker (warning only)
    check_docker || true
    
    # Setup directories
    setup_directories
    
    # Run cleanup if requested
    if [ "$run_clean" = true ]; then
        cleanup
        exit 0
    fi
    
    # Run all checks if no specific checks requested
    if [ "$run_all" = true ]; then
        print_status "Running all checks..."
        
        # Validate project structure first
        validate_project_structure
        
        # Run formatting checks
        run_black_check
        run_ruff_check
        
        # Run linting
        run_pylint
        run_mypy
        
        # Run security checks
        run_security_checks
        
        # Run all tests
        run_tests
        
        # Check coverage
        check_coverage
        
        print_success "All checks completed successfully!"
        
    else
        # Run specific checks
        if [ "$run_structure" = true ]; then
            validate_project_structure
        fi
        
        if [ "$run_format" = true ]; then
            run_black_check
            run_ruff_check
        fi
        
        if [ "$run_lint" = true ]; then
            run_pylint
            run_mypy
        fi
        
        if [ "$run_security" = true ]; then
            run_security_checks
        fi
        
        if [ "$run_test" = true ]; then
            run_tests
        fi
        
        if [ "$run_unit" = true ]; then
            run_unit_tests
        fi
        
        if [ "$run_integration" = true ]; then
            run_integration_tests
        fi
        
        if [ "$run_visual" = true ]; then
            run_visual_tests
        fi
        
        if [ "$run_performance" = true ]; then
            run_performance_tests
        fi
        
        if [ "$run_coverage" = true ]; then
            check_coverage
        fi
    fi
}

# Run main function with all arguments
main "$@"
