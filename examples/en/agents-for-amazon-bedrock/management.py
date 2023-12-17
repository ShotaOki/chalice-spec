import boto3
import sys
from pydantic import BaseModel, Field
from pathlib import Path
import os
from hashlib import md5


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

    @property
    def session(self):
        return boto3.Session(region_name=self.Region)

    @property
    def bucket_name(self):
        return f"agents-{self.stack_name}-{self.Account}-{self.Region}"

    def lambda_arn(self, config: ChaliceConfigFile, stage: str):
        return f"arn:aws:lambda:{self.Region}:{self.Account}:function:{config.app_name}-{stage}"

    @property
    def project_hash(self):
        return md5(self.ChaliceConfig.app_name.encode("utf-8")).hexdigest()[:8]

    @property
    def stack_name(self):
        return f"{self.ChaliceConfig.app_name}_stack".replace("_", "")


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
    create_resource(identity, cfn)

    print("start create stack...")
    waiter = cfn.get_waiter("stack_create_complete")
    waiter.wait(StackName=identity.stack_name)
    print("completed")


def sync():
    pass


def delete():
    identity = read_identity()
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
