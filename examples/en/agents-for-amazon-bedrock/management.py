import boto3
import sys
from pydantic import BaseModel, Field
from pathlib import Path
import os
from hashlib import md5
from app import spec
import json
import io


SCHEMA_FILE = "api-schema.json"
INSTRUCTIONS = "You are an merchant in video game who selling and buying items."
AGENT_VERSION = "DRAFT"
AGENT_ACTION_NAME = "Main"


class ChaliceConfigFile(BaseModel):
    version: str = Field("")
    app_name: str = Field("")


def read_config():
    """
    Read Config File
    """
    with open(str(Path(".chalice") / "config.json")) as fp:
        return ChaliceConfigFile.parse_raw(fp.read())


class CallerIdentity(BaseModel):
    UserId: str
    Account: str
    Arn: str
    Region: str = Field("us-east-1")
    ChaliceConfig: ChaliceConfigFile = Field(ChaliceConfigFile())
    Stage: str = Field("dev")

    @property
    def session(self):
        return boto3.Session(region_name=self.Region)

    @property
    def bucket_name(self):
        return f"agents-for-bedrock-{self.Account}-{self.project_hash}"

    @property
    def lambda_arn(self):
        return f"arn:aws:lambda:{self.Region}:{self.Account}:function:{self.ChaliceConfig.app_name}-{self.Stage}"

    @property
    def lambda_function_name(self):
        return f"{self.ChaliceConfig.app_name}-{self.Stage}"

    @property
    def agents_role_arn(self):
        return f"arn:aws:iam::{self.Account}:role/AmazonBedrockExecutionRoleForAgents_{self.project_hash}"

    @property
    def project_hash(self):
        return md5(self.ChaliceConfig.app_name.encode("utf-8")).hexdigest()[:8]

    @property
    def stack_name(self):
        return f"{self.ChaliceConfig.app_name}_stack".replace("_", "")

    def agent_id_to_arn(self, agent_id: str):
        return f"arn:aws:bedrock:{self.Region}:{self.Account}:agent/{agent_id}"


def read_identity():
    """
    Read Account Identity from STS
    """
    # Current Region
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    session = boto3.Session(region_name=region)
    # Get Account Into
    identity = session.client("sts").get_caller_identity()
    # Parse with pydantic
    item = CallerIdentity.parse_obj(identity)
    # Set Current Region
    item.Region = region
    #
    item.ChaliceConfig = read_config()
    return item


class CurrentAgentInfo(BaseModel):
    agent_id: str
    action_group_id: str


def read_current_agent_info(
    identity: CallerIdentity, bedrock_agent
) -> CurrentAgentInfo:
    agent_ids = [
        item["agentId"]
        for item in bedrock_agent.list_agents()["agentSummaries"]
        if item["agentName"] == identity.ChaliceConfig.app_name
    ]
    if len(agent_ids) == 0:
        print("not found agent")
        return None

    # Get Agent Id
    agent_id = agent_ids[0]
    action_group_ids = [
        item["actionGroupId"]
        for item in bedrock_agent.list_agent_action_groups(
            agentId=agent_id, agentVersion=AGENT_VERSION
        )["actionGroupSummaries"]
        if item["actionGroupName"] == AGENT_ACTION_NAME
    ]
    if len(action_group_ids) == 0:
        print("not found action group")
        return None

    return CurrentAgentInfo(agent_id=agent_id, action_group_id=action_group_ids[0])


def create_resource(identity: CallerIdentity, cfn):
    """
    Create Resource for Agent
    """
    with open("template.yaml") as fp:
        template_body = fp.read()

    parameter = {
        "StackName": identity.stack_name,
        "TemplateBody": template_body,
        "Capabilities": ["CAPABILITY_NAMED_IAM"],
        "Parameters": [
            {"ParameterKey": "HashCode", "ParameterValue": identity.project_hash},
        ],
    }

    try:
        cfn.create_stack(**parameter)
    except Exception:
        cfn.update_stack(**parameter)


def init():
    identity = read_identity()
    cfn = identity.session.client("cloudformation")

    print("start create stack...")
    create_resource(identity, cfn)

    waiter = cfn.get_waiter("stack_create_complete")
    waiter.wait(StackName=identity.stack_name)
    print("stack created")

    print("upload schema file")
    bucket = identity.session.resource("s3").Bucket(identity.bucket_name)
    with io.BytesIO(json.dumps(spec.to_dict()).encode("utf-8")) as fp:
        bucket.upload_fileobj(fp, SCHEMA_FILE)
    print("uploaded schema file")

    print("create agents for amazon bedrock...")
    bedrock_agent = identity.session.client("bedrock-agent")
    response = bedrock_agent.create_agent(
        agentName=identity.ChaliceConfig.app_name,
        agentResourceRoleArn=identity.agents_role_arn,
        instruction=INSTRUCTIONS,
        description="Agents for Amazon Bedrock Sample Project",
        idleSessionTTLInSeconds=900,
        foundationModel="anthropic.claude-v2",
    )
    agent_id = response["agent"]["agentId"]
    print(f"created agents {agent_id}")

    print("create agent action group...")
    bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion=AGENT_VERSION,
        actionGroupName=AGENT_ACTION_NAME,
        description="Agents for Amazon Bedrock Sample Project",
        actionGroupExecutor={"lambda": identity.lambda_arn},
        apiSchema={
            "s3": {"s3BucketName": identity.bucket_name, "s3ObjectKey": SCHEMA_FILE}
        },
        actionGroupState="ENABLED",
    )

    print("add permission to lambda function...")
    identity.session.client("lambda").add_permission(
        Action="lambda:InvokeFunction",
        FunctionName=identity.lambda_function_name,
        Principal="bedrock.amazonaws.com",
        SourceArn=identity.agent_id_to_arn(agent_id),
        StatementId="amazon-bedrock-agent",
    )

    print("completed")


def sync():
    identity = read_identity()
    bedrock_agent = identity.session.client("bedrock-agent")

    print("upload schema file")
    bucket = identity.session.resource("s3").Bucket(identity.bucket_name)
    with io.BytesIO(json.dumps(spec.to_dict()).encode("utf-8")) as fp:
        bucket.upload_fileobj(fp, SCHEMA_FILE)
    print("uploaded schema file")

    agent_info = read_current_agent_info(identity, bedrock_agent)
    if agent_info is None:
        return

    response = bedrock_agent.get_agent_action_group(
        agentId=agent_info.agent_id,
        agentVersion=AGENT_VERSION,
        actionGroupId=agent_info.action_group_id,
    )

    print("update agent action group...")
    bedrock_agent.update_agent_action_group(
        agentId=agent_info.agent_id,
        agentVersion=response["agentActionGroup"]["agentVersion"],
        actionGroupId=response["agentActionGroup"]["actionGroupId"],
        actionGroupName=response["agentActionGroup"]["actionGroupName"],
        description=response["agentActionGroup"]["description"],
        actionGroupExecutor={
            "lambda": response["agentActionGroup"]["actionGroupExecutor"]["lambda"]
        },
        actionGroupState="ENABLED",
        apiSchema={
            "s3": {
                "s3BucketName": response["agentActionGroup"]["apiSchema"]["s3"][
                    "s3BucketName"
                ],
                "s3ObjectKey": response["agentActionGroup"]["apiSchema"]["s3"][
                    "s3ObjectKey"
                ],
            }
        },
    )


def delete():
    identity = read_identity()
    bedrock_agent = identity.session.client("bedrock-agent")
    s3 = identity.session.client("s3")

    print("delete schema file...")
    s3.delete_object(Bucket=identity.bucket_name, Key=SCHEMA_FILE)

    agent_info = read_current_agent_info(identity, bedrock_agent)
    if agent_info is None:
        return

    print("delete agent action group...")
    bedrock_agent.delete_agent_action_group(
        agentId=agent_info.agent_id,
        agentVersion=AGENT_VERSION,
        actionGroupId=agent_info.action_group_id,
        skipResourceInUseCheck=True,
    )

    print("delete agent...")
    bedrock_agent.delete_agent(agentId=agent_info.agent_id, skipResourceInUseCheck=True)

    cfn = identity.session.client("cloudformation")
    cfn.delete_stack(StackName=identity.stack_name)

    print("start delete stack...")
    waiter = cfn.get_waiter("stack_delete_complete")
    waiter.wait(StackName=identity.stack_name)
    print("completed")


if __name__ == "__main__":
    if sys.argv[1] == "init":
        init()
    if sys.argv[1] == "sync":
        sync()
    if sys.argv[1] == "delete":
        delete()
