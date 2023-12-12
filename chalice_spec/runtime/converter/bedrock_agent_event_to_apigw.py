from chalice_spec.runtime.models.bedrock_agent import (
    BedrockAgentEventModel,
)
import json
from chalice_spec.runtime.model_initializer.apigw import initialize_apigw
from . import EventConverter


class BedrockAgentEventToApiGateway(EventConverter):
    def convert_request(self, event):
        """
        parse event input to other type parameter.

        :param event: dict api gateway event
        :return: other type event
        """
        agent_event = BedrockAgentEventModel.from_orm(event)
        apigw_event = initialize_apigw()
        apigw_event.requestContext.httpMethod = agent_event.http_method
        apigw_event.requestContext.resourcePath = agent_event.api_path
        apigw_event.headers["content-type"] = "application/json"
        if agent_event.parameters is not None:
            apigw_event.body = json.dumps(
                {
                    prop.name: prop.value
                    for prop in agent_event.parameters["application/json"]
                }
            )
        else:
            apigw_event.body = json.dumps({})
        return apigw_event.dict()

    def convert_response(self, event, response):
        """
        parse event response to other type response.

        :param event: dict api gateway event
        :param response: dict api gateway response
        :return: other type response
        """
        agent_event = BedrockAgentEventModel.from_orm(event)
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": agent_event.action_group,
                "apiPath": agent_event.api_path,
                "httpMethod": agent_event.http_method,
                "httpStatusCode": response["status_code"],
                "responseBody": {
                    "application/json": {
                        "body": response["body"],
                    },
                },
            },
        }
