"""
Simple Prompt Agent

A minimal example agent demonstrating a clean prompt to LLM service.
Shows how to create a simple agent that just processes text prompts.
Now supports multiple LLM providers and model selection.
"""

from agent_framework import SelfContainedAgent, endpoint, job_model, validate_job_data
from pydantic import BaseModel, Field
from typing import Optional, Literal
from agent import AgentExecutionResult
from services.llm_service import get_unified_llm_service, LLMProvider
from logging_system import get_logger

logger = get_logger(__name__)

@job_model
class PromptJobData(BaseModel):
    """Simple prompt job data model with LLM provider and model selection"""
    prompt: str = Field(
        ...,
        description="Enter your question or request here. Examples: 'Write a summary of renewable energy benefits' or 'Explain quantum computing in simple terms' or 'Create a marketing email for a new product'",
        min_length=1,
        max_length=2000
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider to use (e.g., 'google', 'openai', 'anthropic'). If not specified, the default provider will be used.",
        json_schema_extra={"form_field_type": "llm_provider"}
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use within the provider (e.g., 'gemini-2.0-flash', 'gpt-4'). If not specified, the provider's default model will be used."
    )
    temperature: float = Field(
        default=0.8,
        description="Controls randomness in responses (0.0 = deterministic, 2.0 = very creative)",
        ge=0.0,
        le=2.0
    )
    system_instruction: Optional[str] = Field(
        default=None,
        description="Define the AI's role and behavior. Examples: 'You are a professional copywriter specializing in marketing content' or 'You are a technical expert who explains complex topics clearly' or 'You are a creative writing assistant'",
        max_length=1000
    )
    max_tokens: Optional[int] = Field(
        default=1000,
        description="Maximum number of tokens to generate in the response",
        ge=1,
        le=4000
    )

class SimplePromptAgent(SelfContainedAgent):
    """Simple agent that processes text prompts using any available LLM provider"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="simple_prompt",
            description="A simple agent that processes text prompts using any available LLM provider",
            result_format="markdown",
            **kwargs
        )
        self.llm_service = get_unified_llm_service()
        
    def _get_system_instruction(self) -> str:
        """Return the default system instruction for the agent"""
        return "You are a helpful assistant that processes text prompts and provides useful responses."
        
    async def _execute_job_logic(self, job_data) -> AgentExecutionResult:
        """Execute the job - send prompt to LLM and return response"""
        try:
            # Use custom system instruction if provided, otherwise use default
            system_instruction = job_data.system_instruction or self._get_system_instruction()
            
            # Get provider and model from job data
            provider = job_data.provider
            model = job_data.model
            
            response = await self.llm_service.query(
                prompt=job_data.prompt,
                provider=provider,
                model=model,
                system_instruction=system_instruction,
                temperature=job_data.temperature,
                max_tokens=job_data.max_tokens
            )
            
            # Include provider info in metadata
            provider_used = provider or self.llm_service._default_provider
            
            return AgentExecutionResult(
                success=True,
                result=response,
                metadata={
                    "agent": self.name,
                    "provider": provider_used,
                    "model": model,
                    "temperature": job_data.temperature
                },
                result_format=self.result_format
            )
                
        except Exception as e:
            logger.error(f"Prompt processing failed: {e}")
            return AgentExecutionResult(
                success=False,
                error_message=f"Prompt processing failed: {str(e)}",
                metadata={"agent": self.name}
            )

    @endpoint("/simple-prompt/process", methods=["POST"], auth_required=True)
    async def process_prompt(self, request_data: dict, user: dict):
        """Process a text prompt using any available LLM provider"""
        try:
            job_data = validate_job_data(request_data, PromptJobData)
        except Exception as e:
            # Handle validation errors with proper ApiResponse format
            return self.error_response(
                error_message=f"Validation failed: {str(e)}",
                message="Invalid request data",
                endpoint="/simple-prompt/process"
            )
        
        try:
            # Use custom system instruction if provided, otherwise use default
            system_instruction = job_data.system_instruction or self._get_system_instruction()
            
            # Get provider and model from job data
            provider = job_data.provider
            model = job_data.model
            
            result = await self.llm_service.query(
                prompt=job_data.prompt,
                provider=provider,
                model=model,
                system_instruction=system_instruction,
                temperature=job_data.temperature,
                max_tokens=job_data.max_tokens
            )
            
            # Include provider info in response
            provider_used = provider or self.llm_service._default_provider
            
            return self.success_response(
                result={
                    "response": result,
                    "result_format": self.result_format,
                    "metadata": {
                        "provider": provider_used,
                        "model": model,
                        "temperature": job_data.temperature
                    }
                },
                message="Prompt processed successfully",
                endpoint="/simple-prompt/process",
                provider=provider_used,
                model=model
            )
            
        except Exception as e:
            logger.error(f"Failed to process prompt: {e}")
            return self.error_response(
                error_message=f"Failed to process prompt: {str(e)}",
                message="Prompt processing failed",
                endpoint="/simple-prompt/process"
            )

    @endpoint("/simple-prompt/info", methods=["GET"], auth_required=False)
    async def get_agent_info(self):
        """Get basic agent information including available providers"""
        try:
            available_providers = self.llm_service.get_available_providers()
            
            agent_info = {
                "name": self.name,
                "description": self.description,
                "status": "available",
                "available_providers": available_providers,
                "default_provider": self.llm_service._default_provider,
                "supported_parameters": {
                    "prompt": "Text prompt to send to LLM (required)",
                    "provider": f"LLM provider to use. Options: {', '.join(available_providers)}",
                    "model": "Specific model to use (provider-specific, optional)",
                    "temperature": "Temperature for response generation (0.0-1.0, default: 0.7)",
                    "system_instruction": "Custom system instruction (optional)",
                    "max_tokens": "Maximum tokens to generate (optional)"
                }
            }
            
            return self.success_response(
                result=agent_info,
                message="Agent information retrieved successfully",
                endpoint="/simple-prompt/info"
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return self.error_response(
                error_message=f"Failed to get agent info: {str(e)}",
                message="Agent info retrieval failed",
                endpoint="/simple-prompt/info"
            )

    @endpoint("/simple-prompt/providers", methods=["GET"], auth_required=False)
    async def get_providers_info(self):
        """Get detailed information about all available LLM providers"""
        try:
            providers_info = self.llm_service.get_all_providers_info()
            
            return self.success_response(
                result=providers_info,
                message="Providers information retrieved successfully",
                endpoint="/simple-prompt/providers"
            )
            
        except Exception as e:
            logger.error(f"Failed to get providers info: {e}")
            return self.error_response(
                error_message=f"Failed to get providers info: {str(e)}",
                message="Providers info retrieval failed",
                endpoint="/simple-prompt/providers"
            )

    @endpoint("/simple-prompt/health", methods=["GET"], auth_required=False)
    async def get_health_status(self):
        """Get health status of all LLM providers"""
        try:
            health_status = self.llm_service.get_connection_health_status()
            
            return self.success_response(
                result=health_status,
                message="Health status retrieved successfully",
                endpoint="/simple-prompt/health"
            )
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return self.error_response(
                error_message=f"Failed to get health status: {str(e)}",
                message="Health status retrieval failed",
                endpoint="/simple-prompt/health"
            )

    @endpoint("/simple-prompt/test-connections", methods=["GET"], auth_required=True)
    async def test_all_connections(self):
        """Test connections to all available LLM providers"""
        try:
            connection_tests = self.llm_service.test_all_connections()
            
            return self.success_response(
                result=connection_tests,
                message="Connection tests completed successfully",
                endpoint="/simple-prompt/test-connections"
            )
            
        except Exception as e:
            logger.error(f"Failed to test connections: {e}")
            return self.error_response(
                error_message=f"Failed to test connections: {str(e)}",
                message="Connection tests failed",
                endpoint="/simple-prompt/test-connections"
            ) 