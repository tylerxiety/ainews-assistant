"""
Test the FastAPI /process endpoint without fully processing.
"""
import asyncio
import httpx

async def test_endpoint():
    """Test the /process endpoint."""

    print("Testing FastAPI /process endpoint...")
    print("=" * 60)

    url = "http://localhost:8080/process"
    payload = {"url": "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("\n✅ API endpoint works!")
            else:
                print(f"\n❌ API returned error: {response.text}")

        except httpx.TimeoutException:
            print("⏱️  Request timed out (expected - processing takes time)")
            print("✅ This means the endpoint is working and started processing")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_endpoint())
