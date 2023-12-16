from chalice_spec import APISpec, PydanticPlugin, ChaliceWithSpec, Docs, Operation
from chalice import BadRequestError
from chalicelib.data_type import (
    TalkResponse,
    TalkInput,
    SellOrderResponse,
    SellOrderInput,
    PurchaseOrderResponse,
    PurchaseOrderInput,
)
from random import randint
import json

spec = APISpec(
    title="Purchase Sample Schema",
    openapi_version="3.0.1",
    version="0.1.0",
    plugins=[PydanticPlugin()],
)
app = ChaliceWithSpec(app_name="app_sample_jp_purchase_api", spec=spec)


@app.route(
    "/talk",
    methods=["POST"],
    docs=Docs(
        post=Operation(
            request=TalkInput,
            response=TalkResponse,
        )
    ),
)
def talk_to_shop():
    """
    店主に話しかけます。

    店主からあいさつが返ってきます。
    """
    # 200: OK
    return TalkResponse(message="さあて、どの品物を、買ってくれるのかの？").json()


@app.route(
    "/purchase",
    methods=["POST"],
    docs=Docs(
        post=Operation(
            request=PurchaseOrderInput,
            response=PurchaseOrderResponse,
        )
    ),
)
def purchase():
    """
    店主から装備や品物を購入します。

    購入したい装備の名前と金額を伝えると、装備を購入することができます。
    """
    try:
        input = PurchaseOrderInput.parse_obj(app.current_request.json_body)
    except Exception as e:
        # 400: Bad Request, Response
        raise BadRequestError(e)
    # 200: But, money is not enough to purchase.
    if input.price < 100:
        return PurchaseOrderResponse(
            message=f"ありゃ？{input.price} ゴールド？ それを、買うには、お金が、ちと、足らないようじゃよ"
        ).json()
    # 200: OK
    return PurchaseOrderResponse(
        message=f"ほれっ、{input.name}じゃ。それじゃ、さっそく、装備してみるかの？"
    ).json()


@app.route(
    "/sell",
    methods=["POST"],
    docs=Docs(
        post=Operation(
            request=SellOrderInput,
            response=SellOrderResponse,
        )
    ),
)
def sell():
    """
    店主に装備や品物を売却します。

    売却したい装備の名前を渡すと、店主が適切な金額を支払ってくれます。
    """
    try:
        input = SellOrderInput.parse_obj(app.current_request.json_body)
    except Exception as e:
        # 400: Bad Request, Response
        raise BadRequestError(e)
    price = randint(100, 9999)
    # 200: OK
    return SellOrderResponse(
        price=price,
        message=f"{input.name}じゃったら、{price}ゴールドで、引きとるが、どうじゃ？",
    ).json()


if __name__ == "__main__":
    print(json.dumps(spec.to_dict(), indent=2))
