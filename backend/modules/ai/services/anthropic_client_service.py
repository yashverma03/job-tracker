from datetime import datetime

import anthropic
from anthropic.types import TextBlockParam

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env
from modules.ai.constants.ai_constants import ANTHROPIC_REQUEST_TIMEOUT_SECONDS
from modules.ai.utils.ai_log import log_ai_call

_client = anthropic.Anthropic(api_key=get_env('ANTHROPIC_API_KEY'), timeout=ANTHROPIC_REQUEST_TIMEOUT_SECONDS)


def call_with_forced_tool(
    model: str,
    max_tokens: int,
    system_prompt: str,
    user_prompt: str,
    tool_name: str,
    tool_description: str,
    json_schema: dict,
) -> dict:
    """Call the Anthropic API with a single tool, returning the tool's parsed input.

    Newer models reject tool_choice types "tool"/"any" (400), so the tool is not forced via tool_choice; instead the
    user prompt instructs the model to respond only by calling the tool and a missing tool_use block raises ApiError.

    Shared by every AI service that needs a structured-output response via forced tool use (resume tailoring,
    job scoring, etc.) — keeps client setup, request/response logging, and error handling in one place. The
    system prompt is always cached (1h TTL) since it's static per caller and reused across many requests.
    """
    log_ai_call(f'REQUEST model={model} user_prompt_chars={len(user_prompt)}')

    system_block: TextBlockParam = {
        'type': 'text',
        'text': system_prompt,
        'cache_control': {'type': 'ephemeral', 'ttl': '1h'},
    }

    start = datetime.now()
    try:
        response = _client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[system_block],
            messages=[{'role': 'user', 'content': f'{user_prompt}\n\nRespond only by calling the `{tool_name}` tool.'}],
            tools=[
                {
                    'name': tool_name,
                    'description': tool_description,
                    'input_schema': json_schema,
                },
            ],
            tool_choice={'type': 'auto'},
        )
    except anthropic.APIError as exc:
        elapsed = (datetime.now() - start).total_seconds()
        log_ai_call(f'ERROR elapsed={elapsed:.1f}s {exc}')
        raise ApiError(f'Anthropic API call failed: {exc}', status_code=500) from exc

    elapsed = (datetime.now() - start).total_seconds()
    log_ai_call(f'RESPONSE elapsed={elapsed:.1f}s {response.model_dump_json()}')

    tool_use_block = next((block for block in response.content if block.type == 'tool_use'), None)
    if tool_use_block is None:
        raise ApiError(f'Anthropic API did not return a tool_use block: {response.stop_reason}', status_code=500)

    return tool_use_block.input
