# Technical Debt and Improvements

This document outlines the current technical debt in the codebase and suggests improvements to address these issues.

## Summary

The codebase is generally well-structured with a clear separation of concerns, but there are several areas that need attention:

1. **Dependency Management Issues**: Several instances of tight coupling between components
2. **Temporary Workarounds**: Various temporary solutions that need proper implementation
3. **Incomplete Features**: The review paper functionality is not fully implemented
4. **Database Operations**: Several database operations are marked with TODOs and need implementation
5. **Documentation Gaps**: Some areas lack comprehensive documentation

## Dependency Management Issues

### 1. Direct Service Instantiation in DocumentFormatter
**Issue**: The document formatter directly imports and instantiates the StorageService, creating tight coupling.
**Solution**: Refactor to use dependency injection. Pass the StorageService as a parameter to the DocumentFormatter constructor.
**Priority**: High

### 2. Hardcoded Model Configurations in LLM Service
**Issue**: The LLM service has hardcoded model configurations rather than fully relying on database configuration.
**Solution**: Move all configuration to the database and retrieve it dynamically.
**Priority**: High

### 3. Queue Manager Coupling with Job Processors
**Issue**: The queue manager directly knows about specific job types and their processors.
**Solution**: Implement a more flexible registration system for job processors, allowing new job types to be added without modifying the queue manager.
**Priority**: Medium

### 4. Direct Service Instantiation in Route Handlers
**Issue**: Route handlers often directly instantiate services rather than using dependency injection.
**Solution**: Refactor to use FastAPI's dependency injection system.
**Priority**: Medium

### 5. Subscription Service Coupling with Stripe Service
**Issue**: The subscription service directly depends on the Stripe service implementation.
**Solution**: Create an interface for payment providers to allow for easier testing and future provider changes.
**Priority**: Medium

## Temporary Workarounds

### 1. Paper Credit Usage Recording Workaround
**Issue**: In `subscription_service.py`, there's a temporary workaround for handling missing columns in the saas_paper_credit_usage table.
**Solution**: Properly update the schema and remove the workaround.
**Priority**: High

### 2. Hardcoded Document Storage Paths
**Issue**: In `document_formatter.py`, there are hardcoded paths to output directories.
**Solution**: Move these to configuration, either in the database or environment variables.
**Priority**: High

### 3. Catch-all Exception Handling in Storage Service
**Issue**: In `storage_service.py`, there's a catch-all exception handler that logs errors but returns None, potentially hiding issues.
**Solution**: Implement more specific error handling and propagate errors when appropriate.
**Priority**: Medium

### 4. Dummy Data in My Papers Route
**Issue**: In `main.py`, the `/my-papers` route uses dummy data instead of fetching real data.
**Solution**: Implement proper data retrieval from the database.
**Priority**: High

### 5. Incomplete PDF Conversion Fallback
**Issue**: The PDF conversion in `document_formatter.py` has a placeholder for alternative conversion but doesn't fully implement it.
**Solution**: Implement a robust fallback mechanism for PDF conversion.
**Priority**: Medium

## Incomplete Features

### 1. Review Paper Functionality
**Issue**: The review paper functionality is not fully implemented.
**Solution**: Complete the implementation of the review paper functionality, including content extraction based on file type.
**Priority**: Low (as agreed to focus on research paper functionality first)

### 2. Database Operations in Research Generator
**Issue**: Multiple database operations in db_manager.py are marked with TODOs.
**Solution**: Implement the database operations for insertions, queries, and deletions.
**Priority**: Medium

### 3. Content Extraction Functionality
**Issue**: Content extraction functionality in content_extractor.py is incomplete.
**Solution**: Implement URL checking, metadata storage, and chunk storage.
**Priority**: Medium

## General Improvements

### 1. Comprehensive Testing
**Issue**: The codebase lacks comprehensive test coverage.
**Solution**: Implement unit tests, integration tests, and end-to-end tests for critical functionality.
**Priority**: High

### 2. Improved Documentation
**Issue**: While there are docstrings, they sometimes lack detail on edge cases or implementation specifics.
**Solution**: Enhance documentation throughout the codebase.
**Priority**: Medium

### 3. Consistent Error Handling
**Issue**: Error handling is sometimes verbose and repetitive, and other times minimal.
**Solution**: Implement a consistent approach to error handling across the codebase.
**Priority**: Medium

### 4. Configuration Management
**Issue**: Configuration is spread across environment variables, hardcoded values, and database.
**Solution**: Consolidate configuration management into a single approach, preferably database-driven.
**Priority**: Medium

## Assessment

These issues are all fixable and represent normal technical debt that accumulates during rapid development. None of the issues identified are critical showstoppers, but addressing them will improve the maintainability, testability, and extensibility of the codebase.

The highest priority items to address are:
1. Direct service instantiation in DocumentFormatter
2. Hardcoded model configurations in LLM Service
3. Paper credit usage recording workaround
4. Hardcoded document storage paths
5. Dummy data in My Papers route

These should be addressed before the initial launch to ensure a stable and maintainable codebase.

The medium priority items can be addressed in subsequent iterations after the initial launch.
