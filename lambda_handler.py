import json
import os
from typing import Dict, Any

from mangum import Mangum
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

# Import the FastAPI app
from main import app

# Initialize AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Create the Lambda handler using Mangum
handler = Mangum(
    app,
    lifespan="off",  # Disable lifespan for Lambda
    api_gateway_base_path="/prod",  # Adjust based on your API Gateway stage
    text_mime_types=[
        "application/json",
        "application/javascript",
        "application/xml",
        "application/vnd.api+json",
    ],
)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for Teams Greeting Bot."""
    
    try:
        # Log incoming event (be careful with sensitive data)
        logger.info("Lambda invocation started", 
                   request_id=context.aws_request_id,
                   function_name=context.function_name,
                   remaining_time=context.get_remaining_time_in_millis())
        
        # Add custom metrics
        metrics.add_metric(name="LambdaInvocation", unit=MetricUnit.Count, value=1)
        
        # Extract path and method for logging
        path = event.get("path", "unknown")
        method = event.get("httpMethod", "unknown")
        
        logger.info("Processing request", 
                   path=path, 
                   method=method,
                   user_agent=event.get("headers", {}).get("User-Agent", "unknown"))
        
        # Process the request through Mangum
        response = handler(event, context)
        
        # Log response status
        status_code = response.get("statusCode", 500)
        logger.info("Request processed", 
                   status_code=status_code,
                   path=path,
                   method=method)
        
        # Add metrics for response
        metrics.add_metric(name="ResponseStatusCode", unit=MetricUnit.Count, value=1)
        metrics.add_metadata(key="status_code", value=str(status_code))
        
        return response
        
    except Exception as e:
        # Log error
        logger.error("Lambda execution failed", 
                    error=str(e),
                    request_id=context.aws_request_id)
        
        # Add error metric
        metrics.add_metric(name="LambdaError", unit=MetricUnit.Count, value=1)
        
        # Return error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": "Lambda execution failed",
                "request_id": context.aws_request_id
            })
        }


@tracer.capture_method
def validate_event(event: Dict[str, Any]) -> bool:
    """Validate incoming Lambda event structure."""
    
    required_fields = ["httpMethod", "path"]
    
    for field in required_fields:
        if field not in event:
            logger.error("Missing required field in event", field=field)
            return False
    
    return True


# Alternative handler for testing locally
def local_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Local testing handler that mimics Lambda environment."""
    
    # Mock context if not provided
    if context is None:
        class MockContext:
            aws_request_id = "local-test-request"
            function_name = "teams-greeting-bot-local"
            
            def get_remaining_time_in_millis(self):
                return 300000  # 5 minutes
        
        context = MockContext()
    
    return lambda_handler(event, context)


# Health check for Lambda
@tracer.capture_method
def lambda_health_check() -> Dict[str, Any]:
    """Health check specific for Lambda environment."""
    
    try:
        # Check environment variables
        required_env_vars = [
            "MICROSOFT_APP_ID",
            "MICROSOFT_APP_PASSWORD", 
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            return {
                "status": "unhealthy",
                "missing_environment_variables": missing_vars
            }
        
        return {
            "status": "healthy",
            "service": "Teams Greeting Bot Lambda",
            "environment": "AWS Lambda",
            "runtime": f"python{os.sys.version_info.major}.{os.sys.version_info.minor}"
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        } 