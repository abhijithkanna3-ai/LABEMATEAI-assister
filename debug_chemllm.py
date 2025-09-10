import traceback
import sys
from chemllm_integration import generate_chemllm_response

# Enable more detailed error reporting
sys.excepthook = traceback.print_exc

try:
    print('Test response:', generate_chemllm_response('molecular formula of platinum'))
except Exception as e:
    print(f"Exception type: {type(e)}")
    print(f"Exception message: {e}")
    traceback.print_exc()
