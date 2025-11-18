"""
Faker helper for generating fake data
"""

from faker import Faker


class PurlFaker:
    """Handles fake data generation for purl"""
    
    def __init__(self):
        """Initialize faker"""
        self.faker = Faker()
    
    def generate(self, func_call: str) -> str:
        """
        Generate fake data based on function call
        
        Args:
            func_call: Function call string like "fake.email()" or "fake.random_string(10)"
            
        Returns:
            Generated fake data as string
        """
        # Remove 'fake.' prefix if present
        if func_call.startswith('fake.'):
            func_call = func_call[5:]
        
        # Parse function name and arguments
        if '(' in func_call:
            func_name = func_call[:func_call.index('(')]
            args_str = func_call[func_call.index('(') + 1:func_call.rindex(')')]
            args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
        else:
            func_name = func_call
            args = []
        
        # Handle custom purl functions
        if func_name == 'random_string':
            length = int(args[0]) if args else 10
            return self.faker.pystr(min_chars=length, max_chars=length)
        
        elif func_name == 'random_number':
            length = int(args[0]) if args else 10
            # Generate a number with specified number of digits
            min_val = 10 ** (length - 1)
            max_val = (10 ** length) - 1
            return str(self.faker.random_int(min=min_val, max=max_val))
        
        # Try to call faker method directly
        try:
            method = getattr(self.faker, func_name)
            if callable(method):
                # Convert string args to appropriate types
                converted_args = []
                for arg in args:
                    try:
                        # Try to convert to int
                        converted_args.append(int(arg))
                    except ValueError:
                        # Keep as string
                        converted_args.append(arg)
                
                result = method(*converted_args) if converted_args else method()
                return str(result)
        except AttributeError:
            pass
        
        # If function not found, return the original call
        return f"${{fake.{func_call}}}"
