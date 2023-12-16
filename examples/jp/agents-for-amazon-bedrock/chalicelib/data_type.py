from pydantic import BaseModel, Field


class PurchaseOrderInput(BaseModel):
    """
    店主に伝える購入情報
    """

    name: str = Field(min_length=1, max_length=10, description="購入する装備の名前")
    price: int = Field(ge=1, description="購入で支払う金額、単位はゴールド")


class PurchaseOrderResponse(BaseModel):
    """
    店主からの購入結果のメッセージ
    """

    message: str = Field(description="店主からの購入結果のメッセージ")


class SellOrderInput(BaseModel):
    """
    店主に伝える売却情報
    """

    name: str = Field(min_length=1, max_length=10, description="売却したい品物の名前")


class SellOrderResponse(BaseModel):
    """
    店主からの売却結果のメッセージ
    """

    message: str = Field(description="店主からの売却結果のメッセージ")
    price: int = Field(description="店主が支払った金額、単位はゴールド")


class TalkInput(BaseModel):
    """
    店主に話しかけるための情報
    """

    pass


class TalkResponse(BaseModel):
    """
    店主からのあいさつ
    """

    message: str = Field(description="店主からのあいさつ")
