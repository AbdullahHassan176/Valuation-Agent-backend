"""
Azure Functions app for backend deployment.
This allows the backend to run as serverless functions in Azure Static Web Apps.
"""

import azure.functions as func
import logging
import json
from app.main_azure import app

# Create Azure Functions app
function_app = func.FunctionApp()

@function_app.route(route="api/{*rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main Azure Function that handles all API requests."""
    try:
        # Convert Azure Function request to ASGI scope
        scope = {
            "type": "http",
            "method": req.method,
            "path": req.route_params.get("rest_of_path", ""),
            "query_string": req.url.split("?")[1] if "?" in req.url else "",
            "headers": [(k.lower(), v) for k, v in req.headers.items()],
            "body": await req.get_body(),
        }
        
        # Call the FastAPI app
        response = await app(scope, None, None)
        
        return func.HttpResponse(
            body=response["body"],
            status_code=response["status"],
            headers=dict(response["headers"])
        )
    except Exception as e:
        logging.error(f"Error in Azure Function: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )
