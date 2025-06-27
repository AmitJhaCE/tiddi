import logging
from typing import Dict, List, Any, Optional, Union
from anthropic import AsyncAnthropic
from pydantic import BaseModel, field_validator, Field
import os

# Custom Exceptions
class InvalidConfigError(Exception):
    """Raised when configuration contains invalid keys or structure."""
    pass

class ThinkingTokensExceedMaxError(Exception):
    """Raised when thinking budget tokens exceed max tokens."""
    pass

class InvalidThinkingConfigError(Exception):
    """Raised when thinking configuration is invalid."""
    pass

class InvalidToolConfigError(Exception):
    """Raised when tool configuration is invalid."""
    pass

class InvalidMCPServerConfigError(Exception):
    """Raised when MCP server configuration is invalid."""
    pass

# Content Type Models
class TextContent(BaseModel):
    """Model for text content validation."""
    type: str = "text"
    text: str

class ImageSource(BaseModel):
    """Model for image source validation."""
    type: str = Field(..., pattern=r"^base64$")
    media_type: str = Field(..., pattern=r"^image/(jpeg|png|gif|webp)$")
    data: str

class ImageContent(BaseModel):
    """Model for image content validation."""
    type: str = "image"
    source: ImageSource

class DocumentSource(BaseModel):
    """Model for document source validation."""
    type: str = Field(..., pattern=r"^(url|base64)$")
    url: Optional[str] = None
    media_type: Optional[str] = None
    data: Optional[str] = None
    
    @field_validator('url')
    @classmethod
    def validate_url_source(cls, v, info):
        data = info.data if hasattr(info, 'data') else {}
        if data.get('type') == 'url' and not v:
            raise ValueError('url is required when type is url')
        return v
    
    @field_validator('media_type', 'data')
    @classmethod
    def validate_base64_source(cls, v, info):
        data = info.data if hasattr(info, 'data') else {}
        if data.get('type') == 'base64':
            if info.field_name == 'media_type' and not v:
                raise ValueError('media_type is required when type is base64')
            if info.field_name == 'data' and not v:
                raise ValueError('data is required when type is base64')
        return v

class DocumentContent(BaseModel):
    """Model for document content validation."""
    type: str = "document"
    source: DocumentSource

class ToolUseContent(BaseModel):
    """Model for tool use content validation."""
    type: str = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]

class ToolResultContent(BaseModel):
    """Model for tool result content validation."""
    type: str = "tool_result"
    tool_use_id: str
    content: Any  # Can be string or list of content blocks
    is_error: Optional[bool] = False

class MCPToolUseContent(BaseModel):
    """Model for MCP tool use content validation."""
    type: str = "mcp_tool_use"
    id: str
    name: str
    server_name: str
    input: Dict[str, Any]

class MCPToolResultContent(BaseModel):
    """Model for MCP tool result content validation."""
    type: str = "mcp_tool_result"
    tool_use_id: str
    is_error: bool = False
    content: List[Dict[str, Any]]

# Union type for all content types
ContentBlock = Union[
    TextContent, ImageContent, DocumentContent, 
    ToolUseContent, ToolResultContent, 
    MCPToolUseContent, MCPToolResultContent
]

class Message(BaseModel):
    """Model for message validation supporting both shorthand and full formats."""
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: Union[str, List[ContentBlock]]  # Support both API formats

# Original Configuration Models
class ThinkingConfig(BaseModel):
    """Model for thinking configuration validation."""
    type: str = Field(..., pattern=r"^(enabled|disabled)$")
    budget_tokens: Optional[int] = Field(None, ge=1)
    
    @field_validator('budget_tokens')
    @classmethod
    def validate_budget_tokens(cls, v, info):
        data = info.data if hasattr(info, 'data') else {}
        thinking_type = data.get('type')
        
        if thinking_type == 'enabled' and v is None:
            raise ValueError('budget_tokens is required when thinking is enabled')
        if thinking_type == 'disabled' and v is not None:
            raise ValueError('budget_tokens should not be set when thinking is disabled')
        return v

class ToolProperty(BaseModel):
    """Model for individual tool property validation."""
    type: str
    description: Optional[str] = None

class ToolInputSchema(BaseModel):
    """Model for tool input schema validation."""
    type: str = "object"
    properties: Dict[str, ToolProperty]
    required: List[str] = []

class Tool(BaseModel):
    """Model for tool configuration validation."""
    name: str
    description: str
    input_schema: ToolInputSchema

class ToolConfiguration(BaseModel):
    """Model for MCP server tool configuration."""
    enabled: bool
    allowed_tools: Optional[List[str]] = None

class MCPServer(BaseModel):
    """Model for MCP server configuration validation."""
    type: str = "url"
    url: str
    name: str
    tool_configuration: Optional[ToolConfiguration] = None
    authorization_token: Optional[str] = None

class AnthropicConfig(BaseModel):
    """Main configuration model for validation."""
    model: str
    max_tokens: int = Field(..., ge=1)
    temperature: float = Field(..., ge=0, le=1)
    tools: Optional[List[Tool]] = None
    thinking: Optional[ThinkingConfig] = None
    mcp_servers: Optional[List[MCPServer]] = None

class AnthropicAsyncHandler:
    """
    Async handler for Anthropic API interactions with configuration validation and logging.
    
    This class provides a clean interface for sending messages to Anthropic's Claude API with
    support for tools, thinking mode, and MCP servers. Supports both shorthand text messages
    and full content block format.
    
    Examples:
        Basic usage:
            >>> config = {
            ...     "model": "claude-sonnet-4-20250514",
            ...     "max_tokens": 1000,
            ...     "temperature": 0.7
            ... }
            >>> handler = AnthropicAsyncHandler(config, log_file="claude_calls.log")
            >>> messages = [{"role": "user", "content": "Hello!"}]
            >>> response = await handler.send_messages(messages)
        
        With content blocks:
            >>> messages = [{"role": "user", "content": [
            ...     {"type": "text", "text": "Analyze this image:"},
            ...     {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "..."}}
            ... ]}]
            >>> response = await handler.send_messages(messages)
    """
    
    def __init__(self, config: Dict[str, Any], print_response: bool = True, log_file: Optional[str] = None):
        """
        Initialize the Anthropic async handler.
        
        Args:
            config: Configuration dictionary containing API parameters
            print_response: Whether to print streaming responses to console
            log_file: Path to log file for API call records. If None, logs to console only.
            
        Raises:
            InvalidConfigError: If config contains invalid keys
            ThinkingTokensExceedMaxError: If thinking tokens exceed max tokens
            InvalidThinkingConfigError: If thinking config is malformed
        """
        # Config keys - required or optional
        self._required_config_keys = ["model", "max_tokens", "temperature"]
        self._optional_config_keys = ["tools", "thinking", "mcp_servers"]
        self._accepted_config_keys = self._required_config_keys + self._optional_config_keys
    
        self._verify_config(config)
        self._config = config
        self._print_response = print_response
        
        # Initialize client with lifecycle management
        self._client: Optional[AsyncAnthropic] = None
        self._client_closed = False
        
        # Configure logging
        self._setup_logging(log_file)
        
    async def _get_client(self) -> AsyncAnthropic:
        """Get or create async client with proper lifecycle management."""
        if self._client is None or self._client_closed:
            self._client = AsyncAnthropic(
                timeout=30.0,  # Add reasonable timeout for tests
                max_retries=2 if os.getenv('ENVIRONMENT') == 'testing' else 3  # Fewer retries in tests
            )
            self._client_closed = False
        return self._client
    
    async def close(self):
        """Close the async client and cleanup resources."""
        if self._client and not self._client_closed:
            try:
                await self._client.close()
                self._logger.info("Anthropic client closed successfully")
            except Exception as e:
                self._logger.warning(f"Error closing Anthropic client: {e}")
            finally:
                self._client_closed = True
                self._client = None
                
    def __del__(self):
        """Cleanup when handler is garbage collected."""
        if hasattr(self, '_client') and self._client and not self._client_closed:
            # If we still have an open client, log a warning
            import warnings
            warnings.warn("AnthropicAsyncHandler was garbage collected with open client. Call close() explicitly.")
        
    def _setup_logging(self, log_file: Optional[str]) -> None:
        """
        Configure logging to write to specified file.
        
        Args:
            log_file: Path to log file, or None for console logging only
        """
        # Create a logger specific to this instance
        self._logger = logging.getLogger(f"{__name__}.{id(self)}")
        self._logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplication
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
        else:
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
        
    async def send_messages(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Send messages to Anthropic API and return the response.
        Validates message structure and handles streaming/response.
        
        Args:
            messages: List of message dictionaries (supports both shorthand and full format)
            
        Returns:
            Final message response from the API
            
        Example:
            >>> # Shorthand format
            >>> messages = [{"role": "user", "content": "Hello!"}]
            >>> response = await handler.send_messages(messages)
            >>> 
            >>> # Full content block format
            >>> messages = [{"role": "user", "content": [
            ...     {"type": "text", "text": "Hello!"},
            ...     {"type": "image", "source": {...}}
            ... ]}]
            >>> response = await handler.send_messages(messages)
        """
        # Validate message structure
        self._validate_messages(messages)
        
        # Get client with lifecycle management
        client = await self._get_client()
        
        try:
            async with client.messages.stream(messages=messages, **self._config) as stream:
                if self._print_response:
                    await self._print_stream(stream)
                response = await stream.get_final_message()
                self._log_call_records(response)
                return response
        except Exception as e:
            # Log the error but don't close client immediately - let cleanup handle it
            self._logger.error(f"API call failed: {str(e)}")
            raise

    def _validate_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Validate message structure supports both shorthand and full formats.
        
        Args:
            messages: List of messages to validate
            
        Raises:
            InvalidConfigError: If any message structure is invalid
        """
        try:
            for msg in messages:
                Message(**msg)  # Validates both string and content block formats
        except Exception as e:
            raise InvalidConfigError(f"Message validation failed: {str(e)}")
    
    async def _print_stream(self, stream) -> None:
        """Print streaming response to console with formatted output."""
        async for event in stream:
            if event.type == "content_block_start":
                print()
                if event.content_block.type == "text":
                    print("OUTPUT")
                    print("__"*50)
                    print()
                elif event.content_block.type == "thinking":
                    print("THINKING")
                    print("__"*50) 
                    print()
            elif event.type == "text":
                print(event.text, end="", flush=True)
            elif event.type == "thinking":
                print(event.thinking, end="", flush=True)
            elif event.type == "content_block_stop":
                print()
                
    def _verify_config(self, config: Dict[str, Any]) -> None:
        """
        Verify and validate the configuration dictionary.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            InvalidConfigError: If config contains invalid keys or structure
            ThinkingTokensExceedMaxError: If thinking tokens exceed max tokens
        """
        # Check for missing required keys
        missing_required = set(self._required_config_keys) - set(config.keys())
        if missing_required:
            raise InvalidConfigError(f"Missing required config keys: {missing_required}")
        
        # Check for invalid keys
        invalid_keys = set(config.keys()) - set(self._accepted_config_keys)
        if invalid_keys:
            raise InvalidConfigError(f"Invalid config keys: {invalid_keys}")
        
        try:
            # Validate using pydantic model
            _ = AnthropicConfig(**config)
        except Exception as e:
            raise InvalidConfigError(f"Config validation failed: {str(e)}")
        
        # Special constraint validations
        thinking = config.get("thinking")
        if thinking and thinking.get("type") == "enabled":
            # Auto-correct temperature for thinking mode
            config["temperature"] = 1.0
            
            # Validate thinking tokens don't exceed max tokens
            budget_tokens = thinking.get("budget_tokens", 0)
            max_tokens = config.get("max_tokens", 0)
            if budget_tokens > max_tokens:
                raise ThinkingTokensExceedMaxError(
                    f"Thinking budget tokens ({budget_tokens}) must be less than max tokens ({max_tokens})"
                )
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update the configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates to apply
            
        Raises:
            InvalidConfigError: If updates would create invalid configuration
            ThinkingTokensExceedMaxError: If thinking tokens would exceed max tokens
        """
        # Create a copy of current config and apply updates
        updated_config = self._config.copy()
        updated_config.update(updates)
        
        # Validate the updated configuration
        self._verify_config(updated_config)
        
        # If validation passes, update the instance config
        self._config.update(updates)
        
        self._logger.info(f"Configuration updated with keys: {list(updates.keys())}")
    
    def _log_call_records(self, response: Any) -> None:
        """
        Log API call usage statistics and metadata to the specified log file.
        
        Args:
            response: Response object from Anthropic API containing usage info
        """
        try:
            usage = response.usage
            thinking_config = self._config.get("thinking", {})
            
            log_data = {
                "model": response.model,
                "stop_reason": response.stop_reason,
                "max_tokens": self._config.get("max_tokens"),
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            }
            
            # Add thinking-related info if enabled
            if thinking_config.get("type") == "enabled":
                log_data["thinking_budget_tokens"] = thinking_config.get("budget_tokens")
            
            # Add cache information if available
            if hasattr(usage, 'cache_creation_input_tokens') and usage.cache_creation_input_tokens:
                log_data["cache_creation_input_tokens"] = usage.cache_creation_input_tokens
                
            if hasattr(usage, 'cache_read_input_tokens') and usage.cache_read_input_tokens:
                log_data["cache_read_input_tokens"] = usage.cache_read_input_tokens
            
            # Add server tool usage if available
            if hasattr(usage, 'server_tool_use') and usage.server_tool_use:
                if hasattr(usage.server_tool_use, 'web_search_requests'):
                    log_data["web_search_requests"] = usage.server_tool_use.web_search_requests
            
            # Add service tier if available
            if hasattr(usage, 'service_tier') and usage.service_tier:
                log_data["service_tier"] = usage.service_tier
            
            self._logger.info(f"API Call completed: {log_data}")
            
        except Exception as e:
            self._logger.error(f"Failed to log call records: {str(e)}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get a copy of the current configuration.
        
        Returns:
            Copy of current configuration dictionary
        """
        return self._config.copy()