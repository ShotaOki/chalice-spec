from chalice.app import Chalice
from chalice_spec.runtime.converter.bedrock_agent_event_to_apigw import (
    BedrockAgentEventToApiGateway,
)
from enum import Enum
from typing import List

from chalice_spec.runtime.model_utility.apigw import is_api_gateway_event
from chalice_spec.runtime.model_utility.bedrock_agent import is_bedrock_agent_event


class APIRuntime(Enum):
    """
    Constants: Run on Chalice
    """

    APIGateway = "api-gateway"
    BedrockAgent = "bedrock-agent"


class APIRuntimeHandler:
    """
    Mixin : add __call__ method
    """

    _runtime: List[APIRuntime] = [APIRuntime.APIGateway]

    def set_runtime_handler(self, runtime: APIRuntime | List[APIRuntime]):
        """
        Set Runtime Handler
        Default is invoke by API Gateway
        """
        if isinstance(runtime, list):
            self._runtime = runtime
        else:
            self._runtime = [runtime]

    def __call__(self, event: dict, context: dict):
        """
        This method will be called by lambda event handler.
        event is lambda event, context is lambda context.
        """
        if (APIRuntime.APIGateway in self._runtime) and is_api_gateway_event(event):
            # Called by API Gateway Integration
            return Chalice.__call__(self, event, context)

        converter = None
        # Called by Bedrock Agent
        if (APIRuntime.BedrockAgent in self._runtime) and is_bedrock_agent_event(event):
            converter = BedrockAgentEventToApiGateway()
        # Unknown Caller
        if converter is None:
            # Not found converter
            raise Exception("Not found converter")

        # Invoke parent __call__ method
        api_gateway_response = Chalice.__call__(
            self, event=converter.convert_request(event), context=context
        )
        # Return lambda result
        return converter.convert_response(event, api_gateway_response)
