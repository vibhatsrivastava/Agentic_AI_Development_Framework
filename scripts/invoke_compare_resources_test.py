import sys
import importlib.util
import os
import sys
# Ensure repo root is on sys.path so 'common' package can be imported
sys.path.insert(0, os.path.abspath('.'))
mod_path = os.path.join('projects', '05_terraform_drift_detector', 'src', 'tools', 'diff_tools.py')
spec = importlib.util.spec_from_file_location('diff_tools', mod_path)
diff_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diff_tools)
compare_resources = diff_tools.compare_resources
raw = '{"cloud_resources":{"resource_type":"aws_instance","resources":[{"id":"i-0dcbe8a32d59bbff8","type":"aws_instance","name":"drift-detector-test-instance","tags":{"Name":"drift-detector-test-instance","Project":"drift-detector-demo","ManagedBy":"terraform","Owner":"test-user"},"instance_type":"t2.micro","ami":"ami-09ed39e30153c3bf9","availability_zone":"ap-south-1b","vpc_security_group_ids":["sg-00a12d0fe8a095a43"],"attributes":{"id":"i-0dcbe8a32d59bbff8","instance_type":"t2.micro","ami":"ami-09ed39e30153c3bf9","availability_zone":"ap-south-1b","vpc_security_group_ids":["sg-00a12d0fe8a095a43"],"tags":{"Name":"drift-detector-test-instance","Project":"drift-detector-demo","ManagedBy":"terraform","Owner":"test-user"}}}],"resource_type":"aws_instance"},"payload":{"total_resources":2,"resources":[{"type":"aws_ssm_parameter","name":"amazon_linux_2023_a","id":"/aws/service/ami-amazon-...","tags":[]...}],"payload":"..."},"state_resources":{"..."}'
# Prepare to call the tool; the object is a StructuredTool wrapper
print("Invoking compare_resources with raw payload...")
tool_obj = compare_resources
print("Tool object type:", type(tool_obj))
callable_func = None
for name in ("run", "invoke", "func", "tool_func", "_func", "__call__"):
	if hasattr(tool_obj, name):
		candidate = getattr(tool_obj, name)
		if callable(candidate):
			callable_func = candidate
			print(f"Using callable attribute: {name}")
			break

if callable_func is None:
	# Last resort: if the object itself is callable
	if callable(tool_obj):
		callable_func = tool_obj

if callable_func is None:
	raise RuntimeError("No callable function found on tool object")

res = callable_func(tool_input=raw)
print("Result:", res)
