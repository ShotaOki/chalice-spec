from chalice.app import Chalice
from chalice_spec.runtime.converter.bedrock_agent_event_to_apigw import (
    BedrockAgentEventToApiGateway,
)
from enum import Enum


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

    _runtime: APIRuntime = APIRuntime.APIGateway

    def set_runtime_handler(self, runtime: APIRuntime):
        """
        Set Runtime Handler
        Default is invoke by API Gateway
        """
        self._runtime = runtime

    def __call__(self, event, context):
        """
        This method will be called by lambda event handler.
        event is lambda event, context is lambda context.
        """
        if self._runtime == APIRuntime.APIGateway:
            # Called by API Gateway Integration
            return Chalice.__call__(self, event, context)
        elif self._runtime == APIRuntime.BedrockAgent:
            # Called by Bedrock Agent
            converter = BedrockAgentEventToApiGateway()
        else:
            # Other Integration
            raise Exception("Unknown integration")
        # Invoke parent __call__ method
        api_gateway_response = Chalice.__call__(
            self, event=converter.convert_request(event), context=context
        )
        # Return lambda result
        return converter.convert_response(event, api_gateway_response)
