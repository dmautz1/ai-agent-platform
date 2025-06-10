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
    prompt: str = Field(..., description="Text prompt to send to LLM")
    provider: Optional[LLMProvider] = Field(
        default=None, 
        description="LLM provider to use (google, openai, grok, anthropic, deepseek, llama)",
        json_schema_extra={"form_field_type": "llm_provider"}
    )
    model: Optional[str] = Field(default=None, description="Specific model to use (provider-specific)")
    temperature: float = Field(default=0.8, description="Temperature for response generation")
    system_instruction: Optional[str] = Field(default=None, description="Optional system instruction for the LLM")
    max_tokens: Optional[int] = Field(default=1000, description="Maximum tokens to generate")

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
            
            response = await self.llm_service.query(
                prompt=job_data.prompt,
                provider=job_data.provider,
                model=job_data.model,
                system_instruction=system_instruction,
                temperature=job_data.temperature,
                max_tokens=job_data.max_tokens
            )
            
            # Include provider info in metadata
            provider_used = job_data.provider or self.llm_service._default_provider
            
            return AgentExecutionResult(
                success=True,
                result=response,
                metadata={
                    "agent": self.name,
                    "provider": provider_used,
                    "model": job_data.model,
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
    async def process_prompt(self, request_data: dict, user: dict) -> dict:
        """Process a text prompt using any available LLM provider"""
        job_data = validate_job_data(request_data, PromptJobData)
        
        try:
            # Use custom system instruction if provided, otherwise use default
            system_instruction = job_data.system_instruction or self._get_system_instruction()
            
            result = await self.llm_service.query(
                prompt=job_data.prompt,
                provider=job_data.provider,
                model=job_data.model,
                system_instruction=system_instruction,
                temperature=job_data.temperature,
                max_tokens=job_data.max_tokens
            )
            
            # Include provider info in response
            provider_used = job_data.provider or self.llm_service._default_provider
            
            return {
                "status": "success",
                "result": result,
                "result_format": self.result_format,
                "metadata": {
                    "provider": provider_used,
                    "model": job_data.model,
                    "temperature": job_data.temperature
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process prompt: {e}")
            return {
                "status": "error",
                "error": f"Failed to process prompt: {str(e)}"
            }

    @endpoint("/simple-prompt/info", methods=["GET"], auth_required=False)
    async def get_agent_info(self) -> dict:
        """Get basic agent information including available providers"""
        available_providers = self.llm_service.get_available_providers()
        
        return {
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

    @endpoint("/simple-prompt/providers", methods=["GET"], auth_required=False)
    async def get_providers_info(self) -> dict:
        """Get detailed information about all available LLM providers"""
        return self.llm_service.get_all_providers_info()

    @endpoint("/simple-prompt/health", methods=["GET"], auth_required=False)
    async def get_health_status(self) -> dict:
        """Get health status of all LLM providers"""
        return self.llm_service.get_connection_health_status()

    @endpoint("/simple-prompt/test-connections", methods=["GET"], auth_required=True)
    async def test_all_connections(self) -> dict:
        """Test connections to all available LLM providers"""
        return self.llm_service.test_all_connections() 