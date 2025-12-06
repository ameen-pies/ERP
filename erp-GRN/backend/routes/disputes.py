from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from backend.services.dispute_service import delete_dispute, list_disputes, resolve_dispute, verify_receipt

router = APIRouter(prefix="/api")


@router.get("/disputes")
async def get_disputes() -> list[dict]:
    return await list_disputes()


@router.post("/disputes/{dispute_id}/resolve")
async def resolve_dispute_endpoint(dispute_id: str) -> dict:
    try:
        return await resolve_dispute(dispute_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/disputes/{dispute_id}/verify-receipt")
async def verify_receipt_endpoint(dispute_id: str) -> HTMLResponse:
    """
    Endpoint for supplier to verify receipt of returned quantity.
    This is called when supplier clicks the verification button in the email.
    """
    try:
        result = await verify_receipt(dispute_id)
        # Return a nice HTML confirmation page
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Confirmed</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }
                .container {
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .success-icon {
                    font-size: 64px;
                    color: #4CAF50;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #4CAF50;
                    margin-bottom: 20px;
                }
                p {
                    color: #666;
                    font-size: 16px;
                    margin: 10px 0;
                }
                .info-box {
                    background-color: #f8f9fa;
                    border-left: 4px solid #4CAF50;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                    text-align: left;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>Verification Confirmed</h1>
                <p>Thank you for confirming receipt of the returned items.</p>
                <div class="info-box">
                    <p><strong>The dispute has been automatically resolved.</strong></p>
                    <p>You will receive a confirmation email shortly.</p>
                </div>
                <p style="margin-top: 30px; color: #999; font-size: 14px;">
                    You can close this window now.
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except ValueError as exc:
        # Return error page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .error-icon {{
                    font-size: 64px;
                    color: #dc3545;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #dc3545;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #666;
                    font-size: 16px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">✗</div>
                <h1>Verification Failed</h1>
                <p>{str(exc)}</p>
                <p style="margin-top: 30px; color: #999; font-size: 14px;">
                    Please contact support if you believe this is an error.
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=404)


@router.delete("/disputes/{dispute_id}")
async def delete_dispute_endpoint(dispute_id: str) -> dict:
    try:
        return await delete_dispute(dispute_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

