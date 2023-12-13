import json
from apispec import APISpec
from chalice_spec.chalice import ChaliceWithSpec
from chalice_spec.docs import Docs
from chalice_spec.pydantic import PydanticPlugin
from chalice_spec.runtime.api_runtime import APIRuntime
from tests.schema import TestSchema, AnotherSchema
from pydantic import BaseModel


def setup_test(runtime):
    spec = APISpec(
        title="Test Schema",
        openapi_version="3.0.1",
        version="0.0.0",
        plugins=[PydanticPlugin()],
    )
    app = ChaliceWithSpec(app_name="test", spec=spec, runtime=runtime)
    return app, spec


class APIParameter(BaseModel):
    apiPath: str
    httpMethod: str


def parameter_agents_for_amazon_bedrock(parameter: APIParameter):
    return {
        "messageVersion": "1.0",
        "agent": {
            "name": "string",
            "id": "string",
            "alias": "string",
            "version": "string",
        },
        "inputText": "string",
        "sessionId": "string",
        "actionGroup": "string",
        "apiPath": parameter.apiPath,
        "httpMethod": parameter.httpMethod,
        "parameters": [{"name": "string", "type": "string", "value": "string"}],
        "requestBody": {
            "content": {
                "application/json": {
                    "properties": [
                        {"name": "hello", "type": "string", "value": "hello"},
                        {"name": "world", "type": "int", "value": "123"},
                    ]
                }
            }
        },
        "sessionAttributes": {
            "string": "string",
        },
        "promptSessionAttributes": {"string": "string"},
    }


def parameter_api_gateway(parameter: APIParameter):
    return {
        "resource": parameter.apiPath,
        "path": parameter.apiPath,
        "httpMethod": parameter.httpMethod,
        "requestContext": {
            "resourcePath": parameter.apiPath,
            "httpMethod": parameter.httpMethod,
            "path": parameter.apiPath,
        },
        "headers": {"content-type": "application/json"},
        "multiValueHeaders": {},
        "queryStringParameters": {},
        "multiValueQueryStringParameters": {},
        "pathParameters": {},
        "stageVariables": "",
        "body": json.dumps({"hello": "abc", "world": 123}),
        "isBase64Encoded": False,
    }


def test_invoke_from_agents_for_amazon_bedrock():
    app, spec = setup_test(APIRuntime.BedrockAgent)

    @app.route(
        "/posts",
        methods=["POST"],
        content_types=["application/json"],
        docs=Docs(request=TestSchema, response=AnotherSchema),
    )
    def get_post():
        return AnotherSchema(nintendo="koikoi", atari="game").json()

    response = app(
        parameter_agents_for_amazon_bedrock(
            APIParameter(httpMethod="POST", apiPath="/posts")
        ),
        {},
    )
    assert response["response"]["httpStatusCode"] == 200
    assert (
        "nintendo" in response["response"]["responseBody"]["application/json"]["body"]
    )
    assert "atari" in response["response"]["responseBody"]["application/json"]["body"]
    assert "koikoi" in response["response"]["responseBody"]["application/json"]["body"]


def test_invoke_from_agents_for_api_gateway():
    app, spec = setup_test(APIRuntime.APIGateway)

    @app.route(
        "/posts",
        methods=["POST"],
        content_types=["application/json"],
        docs=Docs(request=TestSchema, response=AnotherSchema),
    )
    def get_post():
        return AnotherSchema(nintendo="koikoi", atari="game").json()

    response = app(
        parameter_api_gateway(APIParameter(httpMethod="POST", apiPath="/posts")),
        {},
    )
    assert response["statusCode"] == 200
    assert "nintendo" in response["body"]
    assert "atari" in response["body"]
    assert "koikoi" in response["body"]
