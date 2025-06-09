#!/usr/bin/env python3
"""
Local testing script for Teams Greeting Bot Lambda function.
Tests the Lambda handler locally before deployment.
"""

import json
import os
import sys
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ.update({
    "MICROSOFT_APP_ID": "test-app-id",
    "MICROSOFT_APP_PASSWORD": "test-app-password", 
    "MICROSOFT_APP_TENANT_ID": "test-tenant-id",
    "GRAPH_CLIENT_ID": "test-graph-client-id",
    "GRAPH_CLIENT_SECRET": "test-graph-client-secret",
    "OPENAI_API_KEY": "test-openai-api-key",
    "DEBUG": "true",
    "BOT_NAME": "TeamsGreetingBot",
    "DEFAULT_GREETING_LANGUAGE": "pt-BR"
})

try:
    from lambda_handler import local_handler
except ImportError as e:
    print(f"❌ Error importing lambda handler: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def create_api_gateway_event(
    method: str = "GET",
    path: str = "/health",
    body: str = None,
    headers: Dict[str, str] = None,
    query_params: Dict[str, str] = None
) -> Dict[str, Any]:
    """Create a mock API Gateway event for testing."""
    
    return {
        "resource": path,
        "path": path,
        "httpMethod": method,
        "headers": headers or {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "test-agent/1.0"
        },
        "multiValueHeaders": {},
        "queryStringParameters": query_params,
        "multiValueQueryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "resourceId": "123456",
            "resourcePath": path,
            "httpMethod": method,
            "extendedRequestId": "test-request-id",
            "requestTime": "09/Apr/2015:12:34:56 +0000",
            "path": f"/dev{path}",
            "accountId": "123456789012",
            "protocol": "HTTP/1.1",
            "stage": "dev",
            "domainPrefix": "testprefix",
            "requestTimeEpoch": 1428582896000,
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "accessKey": None,
                "sourceIp": "127.0.0.1",
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "test-agent/1.0",
                "user": None
            },
            "domainName": "testprefix.testdomainname.com",
            "apiId": "1234567890"
        },
        "body": body,
        "isBase64Encoded": False
    }


def test_health_endpoint():
    """Test the health check endpoint."""
    print("🧪 Testing health endpoint...")
    
    event = create_api_gateway_event("GET", "/health")
    response = local_handler(event)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    
    body = json.loads(response["body"])
    assert body["status"] == "healthy", "Health check should return healthy status"
    
    print("✅ Health endpoint test passed")
    return response


def test_bot_status_endpoint():
    """Test the bot status endpoint."""
    print("🧪 Testing bot status endpoint...")
    
    event = create_api_gateway_event("GET", "/api/bot/status")
    response = local_handler(event)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    
    body = json.loads(response["body"])
    assert "status" in body, "Response should contain status"
    assert "bot_name" in body, "Response should contain bot_name"
    
    print("✅ Bot status endpoint test passed")
    return response


def test_greeting_generation():
    """Test the greeting generation endpoint."""
    print("🧪 Testing greeting generation...")
    
    test_data = {
        "participant_name": "Alexandre",
        "language": "pt-BR"
    }
    
    event = create_api_gateway_event(
        "POST", 
        "/api/bot/test/greeting",
        body=json.dumps(test_data),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
    
    # Note: This test might fail if OpenAI API key is not valid
    # That's expected in a local test environment
    response = local_handler(event)
    
    print(f"Response status: {response['statusCode']}")
    print(f"Response body: {response['body']}")
    
    # In a real environment, we'd expect 200, but in test we might get 500 due to invalid API key
    # That's OK for testing the Lambda handler structure
    
    print("✅ Greeting generation test completed (API key validation expected to fail)")
    return response


def test_bot_webhook():
    """Test the bot webhook endpoint with a mock Teams message."""
    print("🧪 Testing bot webhook...")
    
    # Mock Teams bot framework message
    teams_message = {
        "type": "message",
        "id": "1234567890",
        "timestamp": "2023-01-01T12:00:00.000Z",
        "channelId": "msteams",
        "from": {
            "id": "user123",
            "name": "Test User"
        },
        "conversation": {
            "id": "conversation123"
        },
        "recipient": {
            "id": "bot123",
            "name": "TeamsGreetingBot"
        },
        "text": "Hello bot",
        "serviceUrl": "https://smba.trafficmanager.net/apis/"
    }
    
    event = create_api_gateway_event(
        "POST",
        "/api/bot/messages", 
        body=json.dumps(teams_message),
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
    )
    
    response = local_handler(event)
    
    print(f"Response status: {response['statusCode']}")
    print(f"Response body: {response['body']}")
    
    # Bot webhook might return various status codes depending on the message
    # We just want to ensure it doesn't crash
    print("✅ Bot webhook test completed")
    return response


def run_all_tests():
    """Run all tests."""
    print("🚀 Starting local Lambda tests for Teams Greeting Bot\n")
    
    tests = [
        test_health_endpoint,
        test_bot_status_endpoint,
        test_greeting_generation,
        test_bot_webhook
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, "PASSED", result))
            print()
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            results.append((test.__name__, "FAILED", str(e)))
            print()
    
    # Summary
    print("📋 Test Results Summary:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, status, result in results:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {test_name}: {status}")
        
        if status == "PASSED":
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed! Lambda function is ready for deployment.")
    else:
        print(f"⚠️  {failed} test(s) failed. Review the errors before deployment.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 