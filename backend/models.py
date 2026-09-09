from pydantic import BaseModel


class Bidder(BaseModel):
    company_name: str
    gstin: str
    pan:str
    udyam_number: str
    email: str


class Tender(BaseModel):
    tender_number: str
    title: str
    description: str


class Bid(BaseModel):
    bidder_id: int
    tender_id: int
    bid_amount: float 

class Requirement(BaseModel):
    tender_id: int
    requirement_text: str
    requirement_type: str


class VerificationResult(BaseModel):
    requirement_id: int
    document_id: int
    status: str
    confidence: float
    reason: str


    
