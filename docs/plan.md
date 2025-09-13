# Petit CLI - Implementation Plan

## Milestone 2: Enhanced User Experience and Error Handling 🔄 **IN PROGRESS**

### Phase 1: clone-db Usability Improvements

**Goal**: Improve clone-db command usability with better options and error handling

#### Enhanced Table Handling Options

- [ ] Add `--skip-existing` flag: Skip tables that already exist in destination
  - [ ] Implement logic to check existing tables and skip them
  - [ ] Add appropriate logging messages for skipped tables
  - [ ] Update help documentation for the new flag
  - [ ] Add unit tests for skip-existing functionality

- [ ] Add `--overwrite` flag: Overwrite existing tables in destination
  - [ ] Implement logic to overwrite existing tables
  - [ ] Update `copy_table` function to handle overwrite option
  - [ ] Add confirmation prompt for destructive operations (optional)
  - [ ] Update help documentation for the new flag
  - [ ] Add unit tests for overwrite functionality

- [ ] Update default behavior documentation
  - [ ] Clarify current behavior (error on existing tables)
  - [ ] Update CLI help text to explain all three options
  - [ ] Update interface.md with new options

#### Enhanced Error Handling and Validation

**Source Database Validation**:

- [ ] Add source database existence check before starting clone operation
  - [ ] Implement `validate_source_database()` function
  - [ ] Check if source database exists and is accessible
  - [ ] Provide user-friendly error message for missing/inaccessible source DB
  - [ ] Error message: "Source database does not exist or access denied. Please verify your API key and source endpoint configuration."
  - [ ] Add unit tests for source database validation

**Destination API Authentication Handling**:

- [ ] Add authentication error handling for destination operations
  - [ ] Wrap `pytd.table.Table(dest_client, dest_db, tbl_name)` access with try-catch
  - [ ] Handle write operation authentication errors
  - [ ] Provide user-friendly error message for authentication issues
  - [ ] Error message: "Access denied to destination. Please verify your API key and destination endpoint configuration."
  - [ ] Add unit tests for authentication error handling

#### Code Structure Improvements

- [ ] Refactor error handling into dedicated functions
  - [ ] Create `validate_source_access()` function
  - [ ] Create `validate_destination_access()` function  
  - [ ] Create `handle_authentication_error()` function
  - [ ] Improve separation of concerns in main clone function

#### Testing and Documentation

- [ ] Add comprehensive tests for all new error scenarios
  - [ ] Test source database not found scenarios
  - [ ] Test authentication failure scenarios  
  - [ ] Test skip-existing and overwrite behaviors
  - [ ] Test edge cases and error combinations

- [ ] Update documentation
  - [ ] Update `docs/interface.md` with new options and behaviors
  - [ ] Update README.md with enhanced examples
  - [ ] Update command help text and docstrings

### Phase 2: Performance and Reliability Enhancements (Future)

**Goal**: Optimize performance and improve reliability for large-scale operations

- [ ] Investigate table-level parallelism vs job count configuration
- [ ] Add retry mechanisms for transient failures
- [ ] Implement progress reporting for long-running operations
- [ ] Add dry-run mode for validation before actual operations
- [ ] Implement partial failure recovery (resume functionality)

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
