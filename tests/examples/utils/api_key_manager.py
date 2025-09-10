"""
API Key Management for Examples Testing

Provides secure, interactive API key collection with cost warnings.
"""

import getpass
import os
import sys
from typing import Optional


class APIKeyManager:
    """Manages OpenAI API key collection and validation for testing."""
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.confirmed_cost_awareness = False
    
    def get_api_key(self, force_prompt: bool = False) -> Optional[str]:
        """
        Get OpenAI API key with cost warnings and confirmation.
        
        Args:
            force_prompt: If True, always prompt even if environment variable exists
            
        Returns:
            API key if provided and confirmed, None otherwise
        """
        # Check environment variable first (unless forced to prompt)
        if not force_prompt:
            env_key = os.getenv("OPENAI_API_KEY")
            if env_key:
                print("📋 Found OPENAI_API_KEY in environment")
                if self._confirm_cost_awareness():
                    self.api_key = env_key
                    return env_key
                else:
                    return None
        
        # Interactive API key collection
        print("\n" + "=" * 60)
        print("🔑 OPENAI API KEY REQUIRED FOR LIVE TESTING")
        print("=" * 60)
        print("⚠️  WARNING: Live tests make REAL API calls that cost money!")
        print("💰 Estimated cost: ~$0.05-$0.20 for full test suite")
        print("🛡️  Cost controls: Max 5 API calls per framework")
        print("⏱️  Timeout protection: 30 seconds max per call")
        print("\n📝 Your API key will not be stored or logged")
        print("🔒 Enter 'quit' to exit without testing")
        print("-" * 60)
        
        try:
            api_key = getpass.getpass("Enter your OpenAI API key: ").strip()
            
            if api_key.lower() in ['quit', 'q', 'exit']:
                print("❌ Testing cancelled by user")
                return None
            
            if not api_key:
                print("❌ No API key provided")
                return None
            
            if not api_key.startswith('sk-'):
                print("⚠️  Warning: API key doesn't start with 'sk-' (unusual format)")
                confirm = input("Continue anyway? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    return None
            
            if self._confirm_cost_awareness():
                self.api_key = api_key
                return api_key
            else:
                return None
                
        except KeyboardInterrupt:
            print("\n❌ Testing cancelled by user")
            return None
        except Exception as e:
            print(f"❌ Error collecting API key: {e}")
            return None
    
    def _confirm_cost_awareness(self) -> bool:
        """Confirm user understands the cost implications."""
        if self.confirmed_cost_awareness:
            return True
        
        print("\n💡 COST CONFIRMATION REQUIRED")
        print("By proceeding, you acknowledge:")
        print("  • Real OpenAI API calls will be made")
        print("  • These calls will incur charges to your OpenAI account")
        print("  • Estimated cost: $0.05-$0.20 for full test suite")
        print("  • You can stop tests at any time with Ctrl+C")
        
        try:
            confirm = input("\nProceed with live API testing? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                self.confirmed_cost_awareness = True
                print("✅ Cost awareness confirmed - proceeding with tests")
                return True
            else:
                print("❌ Testing cancelled - cost not confirmed")
                return False
        except KeyboardInterrupt:
            print("\n❌ Testing cancelled by user")
            return False
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Basic validation of API key format.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if format appears valid, False otherwise
        """
        if not api_key:
            return False
        
        # Basic format check
        if not isinstance(api_key, str):
            return False
        
        # Check length (OpenAI keys are typically 51 characters)
        if len(api_key) < 20:
            return False
        
        # Could add more validation here if needed
        return True
    
    def clear_api_key(self):
        """Clear stored API key for security."""
        self.api_key = None
        self.confirmed_cost_awareness = False


def get_test_api_key(force_prompt: bool = False) -> Optional[str]:
    """
    Convenience function to get API key for testing.
    
    Args:
        force_prompt: If True, always prompt even if environment variable exists
        
    Returns:
        API key if provided and confirmed, None otherwise
    """
    manager = APIKeyManager()
    return manager.get_api_key(force_prompt=force_prompt)


if __name__ == "__main__":
    # Test the API key manager
    print("Testing API Key Manager...")
    api_key = get_test_api_key(force_prompt=True)
    if api_key:
        print(f"✅ API key collected: {api_key[:10]}...")
    else:
        print("❌ No API key collected")
