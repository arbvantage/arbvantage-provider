# Changelog

## [Unreleased] - 2025-07-30

### Added
- **Unified Response Format**: All response types (success, error, limit) now have a consistent structure with metadata
- **Metadata Fields**: Every response now includes provider name, action name, timezone, and timestamps
- **Enhanced Traceability**: Better debugging and monitoring capabilities with standardized response format

### Changed
- **Response Structure**: Modified `_handle_response` method to always include metadata fields
- **Error Handling**: Updated error responses to include consistent metadata structure
- **Rate Limit Responses**: Rate limit responses now follow the same unified format
- **Documentation**: Updated README.md with new unified response format examples

### Technical Details
- Modified `arbvantage_provider/provider.py`:
  - Updated `_handle_response` method to always add metadata
  - Ensured all response types (success, error, limit) pass through `_handle_response`
  - Unified error field naming from `"errors"` to `"error"`
- Updated `arbvantage_provider/schemas.py`:
  - Confirmed support for `"limit"` status in `ProviderResponse` schema
- Updated documentation in `README.md`:
  - Added comprehensive examples of unified response format
  - Documented metadata fields and their purposes
  - Added benefits section explaining the advantages of unified format

### Response Format Changes
**Before:**
```python
# Success response
{
    "status": "success",
    "data": {"result": "data"}
}

# Error response  
{
    "status": "error",
    "message": "Error occurred",
    "data": {"error": "details"}
}
```

**After:**
```python
# All response types now have consistent structure
{
    "status": "success|error|limit",
    "message": "Description",
    "data": {
        "provider": "provider_name",
        "action": "action_name", 
        "timezone": "timezone",
        "now": "2024-03-20T10:30:00+03:00",
        "now_utc": "2024-03-20T07:30:00+00:00",
        "response": {"actual_data_or_error_details"}
    }
}
```

### Benefits
1. **Consistency**: All response types have identical structure
2. **Traceability**: Every response includes provider, action, and timestamp info
3. **Debugging**: Easy to identify source of responses
4. **Monitoring**: Better logging and monitoring capabilities
5. **Integration**: External systems can rely on consistent format 