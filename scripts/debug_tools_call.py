import sys, os, importlib.util, json
# Ensure repo root
sys.path.insert(0, os.path.abspath('.'))

# Load modules
mod_paths = {
    'terraform_tools': 'projects/05_terraform_drift_detector/src/tools/terraform_tools.py',
    'aws_tools': 'projects/05_terraform_drift_detector/src/tools/aws_tools.py',
    'diff_tools': 'projects/05_terraform_drift_detector/src/tools/diff_tools.py',
}
modules = {}
for name, p in mod_paths.items():
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    modules[name] = m

parse_state_tool = modules['terraform_tools'].parse_terraform_state
fetch_cloud_tool = modules['aws_tools'].fetch_cloud_resources
compare_tool = modules['diff_tools'].compare_resources

state_path = 'projects/05_terraform_drift_detector/test_infrastructure/terraform.tfstate'
print('Invoking parse_terraform_state...')
# call underlying func if available
if hasattr(parse_state_tool, 'func'):
    res = parse_state_tool.func(file_path=state_path)
else:
    res = parse_state_tool(file_path=state_path)
print('parse_terraform_state output (truncated):')
print(res[:1000])

print('\nInvoking fetch_cloud_resources...')
# Use instance id from parsed state
instance_id = None
try:
    parsed_tmp = json.loads(res) if isinstance(res, str) else res
    for r in parsed_tmp.get('resources', []):
        if r.get('type') == 'aws_instance' and r.get('id'):
            instance_id = r.get('id')
            break
except Exception:
    pass

if not instance_id:
    raise RuntimeError('No instance id found in parsed state')

if hasattr(fetch_cloud_tool, 'func'):
    cres = fetch_cloud_tool.func(resource_ids=instance_id, resource_type='aws_instance')
else:
    cres = fetch_cloud_tool(resource_ids=instance_id, resource_type='aws_instance')
print('fetch_cloud_resources output (truncated):')
print(cres[:1000])

print('\nNow calling compare_resources with parsed outputs...')
# If parse returned a JSON string, parse it
try:
    if isinstance(res, str):
        parsed_state = json.loads(res)
    else:
        parsed_state = res
except Exception:
    parsed_state = res

try:
    if isinstance(cres, str):
        parsed_cloud = json.loads(cres)
    else:
        parsed_cloud = cres
except Exception:
    parsed_cloud = cres

# If cloud fetch failed due to missing creds, simulate cloud resource with missing Environment tag
if isinstance(parsed_cloud, dict) and parsed_cloud.get('error'):
    print('Simulating cloud resources with missing Environment tag for drift scenario')
    # Build cloud resource matching parsed_state instance but without Environment tag
    state_resources_list = parsed_state.get('resources', []) if isinstance(parsed_state, dict) else parsed_state
    simulated_resources = []
    for r in state_resources_list:
        if r.get('type') == 'aws_instance':
            sim = {
                'id': r.get('id'),
                'type': 'aws_instance',
                'name': r.get('name') or r.get('attributes', {}).get('name', ''),
                'tags': {k: v for k, v in (r.get('tags') or {}).items() if k != 'Environment'},
                'attributes': {**(r.get('attributes') or {})}
            }
            # Also remove Environment from attributes.tags if present
            if 'tags' in sim['attributes']:
                sim['attributes']['tags'] = {k: v for k, v in sim['attributes']['tags'].items() if k != 'Environment'}
            simulated_resources.append(sim)
    parsed_cloud = {'resource_type': 'aws_instance', 'resources': simulated_resources}

# Call compare func with parsed state resources and simulated cloud resources
if hasattr(compare_tool, 'func'):
    out = compare_tool.func(state_resources=parsed_state.get('resources') if isinstance(parsed_state, dict) else parsed_state,
                             cloud_resources=parsed_cloud.get('resources') if isinstance(parsed_cloud, dict) else parsed_cloud,
                             payload=None)
else:
    out = compare_tool(state_resources=parsed_state.get('resources') if isinstance(parsed_state, dict) else parsed_state,
                       cloud_resources=parsed_cloud.get('resources') if isinstance(parsed_cloud, dict) else parsed_cloud,
                       payload=None)

print('\ncompare_resources output:')
print(out)
