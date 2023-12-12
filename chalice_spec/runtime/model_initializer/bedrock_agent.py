from chalice_spec.runtime.models.bedrock_agent import BedrockAgentEventModel


def initialize_bedrock_agent() -> BedrockAgentEventModel:
    """
    Create empty bedrock agent event.
    """
    return BedrockAgentEventModel.from_orm({})
