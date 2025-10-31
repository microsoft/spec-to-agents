# Bing Search AI Function Wrapper Design

## Overview

Create a custom `@ai_function` wrapper for Bing Web Search API that provides properly formatted, LM-friendly search results. This tool will enable agents to search the web and receive structured responses optimized for language model consumption.

## Purpose

Enable agents in the event planning workflow to search the web for current information (venue details, catering options, etc.) using a consistent tool pattern that matches other custom tools (weather, calendar).

## Design Decisions

### Approach: Direct Azure Cognitive Services SDK

**Selected:** Approach 1 - Direct Azure Cognitive Services SDK with `@ai_function` wrapper

**Rationale:**
- Maintains consistency with existing custom tools (weather, calendar)
- Provides full control over response formatting for LM consumption
- Simple implementation with low complexity
- Direct API access with minimal latency

**Alternatives Considered:**
- httpx REST API approach (rejected: adds complexity without benefits)
- Wrapper around HostedWebSearchTool (rejected: unnecessary layering, requires Foundry setup)

## Architecture

### Function Signature

```python
@ai_function
async def web_search(
    query: Annotated[str, Field(description="Search query")],
    count: Annotated[int, Field(description="Number of results (1-50)", ge=1, le=50)] = 10,
) -> str:
```

### Parameters

- **query** (str, required): The search query string
- **count** (int, optional): Number of results to return (1-50), default 10

### Response Format

Structured text optimized for LM parsing:

```
Found [N] results for "[query]":

1. [Title]
   [Snippet/Description]
   URL: [url]
   Source: [display_url]

2. [Title]
   [Snippet/Description]
   URL: [url]
   Source: [display_url]
```

**Format Benefits:**
- Clear result count at top
- Numbered results for easy reference in agent responses
- Distinct sections (title, snippet, URL, source)
- Clean whitespace separation
- Human and LM readable

### Error Handling

| Scenario | Handling | Return Value |
|----------|----------|--------------|
| Missing API key | Raise `ValueError` at module load | N/A (fails fast) |
| API HTTP errors | Catch and format | `"Error: [status] - [message]"` |
| No results found | Return informative message | `"No results found for query: [query]"` |
| Network errors | Catch exception | `"Error connecting to Bing Search: [error]"` |
| Invalid count | Pydantic validation | Automatic validation error |

## Implementation Details

### Dependencies

- `azure-cognitiveservices-search-websearch>=2.0.1` (already in project)
- `msrest>=0.7.0` (transitive dependency)
- `agent_framework` (for `@ai_function` decorator)
- `pydantic` (for `Field` annotations)

### Environment Configuration

**Required Environment Variable:**
```bash
BING_SEARCH_API_KEY=<your_api_key>
```

**Obtaining API Key:**
1. Azure Portal → Create "Bing Search v7" resource
2. Navigate to resource → Keys and Endpoint
3. Copy Key 1 or Key 2

### SDK Integration

**Client Initialization:**
```python
from azure.cognitiveservices.search.websearch import WebSearchClient
from msrest.authentication import CognitiveServicesCredentials

client = WebSearchClient(
    endpoint="https://api.bing.microsoft.com",
    credentials=CognitiveServicesCredentials(api_key),
)
```

**API Call:**
```python
response = client.web.search(query=query, count=count)
```

**Response Structure:**
- `response.web_pages.value` - list of results
  - `.name` - page title
  - `.snippet` - text description
  - `.url` - full URL
  - `.display_url` - human-readable URL

### Response Parsing Logic

1. Check if `response.web_pages` exists
2. Extract `value` list (can be None or empty)
3. If no results, return "No results found" message
4. Otherwise, format each result:
   - Use result number (1-indexed)
   - Title from `.name`
   - Snippet from `.snippet`
   - Full URL from `.url`
   - Display URL from `.display_url`
5. Join with double newlines for clear separation

## Integration

### Module Export

Update `src/spec_to_agents/tools/__init__.py`:
```python
from .bing_search import web_search

__all__ = [
    # ... existing exports
    "web_search",
]
```

### Agent Usage

Agents can use the tool by importing and including in their tools list:

```python
from agent_framework import ChatAgent
from ..tools import web_search

agent = ChatAgent(
    name="Venue Specialist",
    tools=[web_search, ...],
    ...
)
```

## Testing Strategy

### Unit Tests

**File:** `tests/test_tools_bing_search.py`

**Test Cases:**
1. Successful search with results
2. Search with no results
3. API error handling (HTTP 403, 429, 500)
4. Network error handling
5. Invalid count parameter (Pydantic validation)
6. Response formatting verification

**Mocking Strategy:**
Mock `WebSearchClient.web.search()` to return controlled responses

### Manual Testing

**DevUI Test:**
1. Start DevUI: `uv run app`
2. Select agent with web_search tool
3. Query: "Search for wedding venues in Seattle"
4. Verify structured response with results

**Direct Test:**
```bash
uv run python -c "import asyncio; from src.spec_to_agents.tools.bing_search import web_search; print(asyncio.run(web_search('Microsoft Agent Framework')))"
```

Expected: Formatted search results with titles, snippets, and URLs

## Security Considerations

- API key stored in `.env` file (not committed to git)
- Add `BING_SEARCH_API_KEY` to `.env.example` with placeholder
- Consider Azure Managed Identity for production deployments
- API key visible in error messages - ensure proper logging hygiene

## Performance Considerations

- **Latency:** ~100-500ms per API call (depends on query complexity)
- **Rate Limits:** Bing Search has query/second limits based on tier
- **Caching:** Consider adding caching for repeated queries (future enhancement)
- **Async:** Properly async to avoid blocking event loop

## Future Enhancements

1. **Result Filtering:**
   - Add `site:` parameter to filter by domain
   - Add `freshness` parameter for recent results only
   - Add `market` parameter for localized results

2. **Enhanced Parsing:**
   - Include page publish date when available
   - Extract rich snippets/structured data
   - Include image results for visual queries

3. **Caching:**
   - Add TTL-based cache for repeated queries
   - Reduce API costs and improve latency

4. **Grounding/Citations:**
   - Add citation markers [1], [2], etc.
   - Build citation list for reference

## Verification Checklist

- [ ] API key loaded from environment
- [ ] Async function properly implemented
- [ ] Response formatted for LM readability
- [ ] Error handling for all edge cases
- [ ] Unit tests pass (100% coverage)
- [ ] Manual testing in DevUI successful
- [ ] Documentation updated (docstring, type hints)
- [ ] Exported in `__init__.py`
- [ ] `.env.example` updated

## References

- [Bing Web Search API Documentation](https://docs.microsoft.com/azure/cognitive-services/bing-web-search/)
- [Azure Cognitive Services Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/cognitiveservices/azure-cognitiveservices-search-websearch)
- Project tool patterns: `src/spec_to_agents/tools/weather.py`, `src/spec_to_agents/tools/calendar.py`
