# Petit CLI - Implementation Plan

## Milestone 2: Enhanced User Experience and Error Handling 🔄 **IN PROGRESS**

### Phase 1: clone-db Usability Improvements

**Goal**: Improve clone-db command usability with better options and error handling

#### Enhanced Table Handling Options

- [x] Add `--skip-existing` flag: Skip tables that already exist in destination
  - [x] Implement logic to check existing tables and skip them
  - [x] Add appropriate logging messages for skipped tables
  - [x] Update help documentation for the new flag
  - [x] Add unit tests for skip-existing functionality

- [x] Add `--overwrite` flag: Overwrite existing tables in destination
  - [x] Implement logic to overwrite existing tables
  - [x] Update `copy_table` function to handle overwrite option
  - [ ] Add confirmation prompt for destructive operations (optional)
  - [x] Update help documentation for the new flag
  - [x] Add unit tests for overwrite functionality

- [x] Update default behavior documentation
  - [x] Clarify current behavior (error on existing tables)
  - [x] Update CLI help text to explain all three options
  - [x] Update interface.md with new options

#### Enhanced Error Handling and Validation

**Source Database Validation**:

- [x] Add source database existence check before starting clone operation
  - [x] Implement `validate_source_database()` function (using `client.exists()`)
  - [x] Check if source database exists and is accessible
  - [x] Provide user-friendly error message for missing/inaccessible source DB
  - [x] Error message: "Source database does not exist or access denied. Please verify your API key and source endpoint configuration."
  - [x] Add unit tests for source database validation

**Destination API Authentication Handling**:

- [x] Add authentication error handling for destination operations
  - [x] Wrap `pytd.table.Table(dest_client, dest_db, tbl_name)` access with try-catch
  - [x] Handle write operation authentication errors
  - [x] Provide user-friendly error message for authentication issues
  - [x] Error message: "Authentication failed for destination table. Please verify your API key and destination endpoint configuration."
  - [x] Add unit tests for authentication error handling

#### Code Structure Improvements

- [x] Refactor error handling into dedicated functions
  - [x] Create `validate_source_database()` function (using proper `client.exists()`)
  - [x] Remove unnecessary destination validation (handled at operation time)
  - [x] Improve separation of concerns in main clone function
  - [x] Remove unnecessary client initialization error handling

#### Testing and Documentation

- [x] Add comprehensive tests for all new error scenarios
  - [x] Test source database not found scenarios
  - [x] Test authentication failure scenarios  
  - [x] Test skip-existing and overwrite behaviors
  - [x] Test edge cases and error combinations

- [x] Update documentation
  - [x] Update `docs/interface.md` with new options and behaviors
  - [x] Update command help text and docstrings
  - [x] Update README.md with enhanced examples

### Phase 2: Performance and Reliability Enhancements ✅ **COMPLETED**

**Goal**: Optimize performance and improve reliability for large-scale operations

- [x] **Implement table-level parallelism with configurable parameters**
  - [x] Add `--table-parallelism` option (default: 2) for concurrent table processing
  - [x] Add `--download-parallelism` option (default: 4) for parallel downloads per table
  - [x] Add `--chunk-size` option (default: 10,000) for memory-efficient processing
  - [x] Update ThreadPoolExecutor to use configurable table parallelism

- [x] **Migrate from pytd.query to tdclient.query with parallel downloads**
  - [x] Replace `pytd.query` with direct `tdclient.query` usage
  - [x] Implement `job.result_format()` with parallel download support
  - [x] Add chunked processing to avoid memory issues with large tables
  - [x] Implement progress logging for long-running operations

- [x] **Enhanced chunked data processing**
  - [x] Create `_process_table_chunks()` helper function
  - [x] Create `_write_chunk_to_destination()` helper function
  - [x] Implement memory-efficient streaming data processing
  - [x] Add periodic progress reporting during chunk processing

- [x] **Update tests for new parallel processing functionality**
  - [x] Add tests for custom parallelism settings
  - [x] Update existing tests to mock tdclient properly
  - [x] Fix test mocking for new tdclient-based implementation
  - [x] Ensure all tests pass with new parallel processing logic

**Implementation Details**:

- **Hybrid parallelization strategy**: Combines table-level (2 concurrent) and download-level (4 concurrent) parallelism
- **Memory efficiency**: Processes data in 10,000-row chunks to avoid loading entire tables into memory
- **Progress monitoring**: Logs progress every 10 chunks during processing
- **Backward compatibility**: All existing functionality and CLI options preserved

### Phase 3: Additional Reliability Features (Future)

**Goal**: Add retry mechanisms, progress reporting, and recovery features

- [ ] Add retry mechanisms for transient failures
- [ ] Implement progress reporting for long-running operations
- [ ] Add dry-run mode for validation before actual operations
- [ ] Implement partial failure recovery (resume functionality)
- [ ] Add pyright for comprehensive type checking to improve code quality and catch type-related bugs

### Phase 3: Additional User Experience Improvements (Future)

**Goal**: Further enhance usability based on user feedback

- [ ] Add interactive mode for confirmation of destructive operations
- [ ] Implement table filtering options (include/exclude patterns)
- [ ] Add support for selective column copying
- [ ] Implement bandwidth throttling options
- [ ] Add detailed progress reporting and ETA calculations

---

## Success Criteria for Milestone 2

**Functionality**:

- [ ] Users can handle existing destination databases gracefully with multiple options
- [ ] Clear, actionable error messages guide users to resolve authentication/access issues
- [ ] Source database validation prevents wasted time on invalid operations

**Usability**:

- [ ] Error messages are clear and actionable in English
- [ ] Command options are intuitive and well-documented
- [ ] Help text clearly explains all available behaviors

**Reliability**:

- [ ] Robust error handling prevents unexpected crashes
- [ ] Authentication issues are caught early with clear guidance
- [ ] Edge cases are handled gracefully with appropriate messages

**Testing**:

- [ ] >90% test coverage for all new functionality
- [ ] All error scenarios have corresponding tests
- [ ] Integration tests cover real-world usage patterns

---

## Notes

- Documentation files may be versioned for different development phases
- Maintain backward compatibility unless explicitly breaking changes are needed
- Focus on user experience and clear error messaging
- Prioritize reliability and data safety for database operations
