from chalice_spec.runtime.models.apigw import APIGatewayProxyEventModel


def initialize_apigw() -> APIGatewayProxyEventModel:
    """
    Create empty api gateway event.
    """
    return APIGatewayProxyEventModel.from_orm(
        {
            "resource": "/my/path",
            "path": "/my/path",
            "httpMethod": "GET",
            "headers": {},
            "multiValueHeaders": {},
            "queryStringParameters": {},
            "multiValueQueryStringParameters": {},
            "requestContext": {
                "accountId": "",
                "apiId": "",
                "authorizer": {},
                "httpMethod": "GET",
                "identity": {},
                "path": "/my/path",
                "protocol": "HTTP/1.1",
                "requestId": "id=",
                "requestTime": "04/Mar/2020:19:15:17 +0000",
                "requestTimeEpoch": 1583349317135,
                "resourcePath": "/my/path",
                "stage": "$default",
            },
            "body": "",
            "isBase64Encoded": False,
        }
    )
