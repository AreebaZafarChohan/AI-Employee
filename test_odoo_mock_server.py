from fastapi import FastAPI, Request
import uvicorn
import json

app = FastAPI()

@app.post("/jsonrpc")
async def jsonrpc(request: Request):
    body = await request.json()
    method = body.get("params", {}).get("method")
    service = body.get("params", {}).get("service")
    
    # Auth
    if service == "common" and method == "authenticate":
        return {"jsonrpc": "2.0", "id": body.get("id"), "result": 123} # Return UID 123
    
    # Execute (Invoices/Partners)
    if service == "object" and method == "execute_kw":
        model = body["params"]["args"][3]
        call_method = body["params"]["args"][4]
        
        if model == "account.move" and call_method == "search_read":
            return {
                "jsonrpc": "2.0", 
                "id": body.get("id"), 
                "result": [
                    {
                        "id": 1,
                        "name": "INV/2026/0001",
                        "partner_id": [10, "Delta Corp"],
                        "invoice_date_due": "2026-03-01",
                        "amount_total": 5500.0,
                        "amount_residual": 5500.0,
                        "currency_id": [1, "USD"],
                        "move_type": "out_invoice"
                    },
                    {
                        "id": 2,
                        "name": "BILL/2026/0005",
                        "partner_id": [20, "Cloud Services Inc"],
                        "invoice_date": "2026-03-10",
                        "amount_total": 2500.0,
                        "currency_id": [1, "USD"],
                        "move_type": "in_invoice"
                    }
                ]
            }
        
        if model == "res.partner" and call_method == "search_read":
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": [
                    {"id": 10, "name": "Delta Corp", "email": "finance@delta.com"},
                    {"id": 20, "name": "Cloud Services Inc", "email": "billing@cloud.com"}
                ]
            }
            
    return {"jsonrpc": "2.0", "id": body.get("id"), "result": []}

if __name__ == "__main__":
    print("🚀 Starting Mock Odoo Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
