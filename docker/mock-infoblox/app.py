#!/usr/bin/env python3
"""
Mock Infoblox WAPI Server for Testing
Implements minimal WAPI v2.12.3 endpoints needed for sync testing
"""

from flask import Flask, jsonify, request, Response
from functools import wraps
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Mock database
HOST_RECORDS = [
    {
        "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5leGFtcGxlLmhvc3Qx:host1.example.com/default",
        "name": "host1.example.com",
        "ipv4addrs": [{"ipv4addr": "192.168.1.10"}],
        "extattrs": {"Site": {"value": "DC1"}},
        "comment": "Test host 1"
    },
    {
        "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5leGFtcGxlLmhvc3Qy:host2.example.com/default",
        "name": "host2.example.com",
        "ipv4addrs": [{"ipv4addr": "192.168.1.11"}],
        "extattrs": {"Site": {"value": "DC1"}},
        "comment": "Test host 2"
    },
    {
        "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5leGFtcGxlLmhvc3Qz:host3.example.com/default",
        "name": "host3.example.com",
        "ipv4addrs": [{"ipv4addr": "192.168.1.12"}],
        "extattrs": {"Site": {"value": "DC2"}},
        "comment": "Test host 3"
    },
    {
        "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5leGFtcGxlLnNlcnZlcjE:server1.example.com/default",
        "name": "server1.example.com",
        "ipv4addrs": [{"ipv4addr": "192.168.2.10"}],
        "extattrs": {"Site": {"value": "DC1"}, "Environment": {"value": "Production"}},
        "comment": "Production server 1"
    },
    {
        "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5leGFtcGxlLnNlcnZlcjI:server2.example.com/default",
        "name": "server2.example.com",
        "ipv4addrs": [{"ipv4addr": "192.168.2.11"}],
        "extattrs": {"Site": {"value": "DC2"}, "Environment": {"value": "Production"}},
        "comment": "Production server 2"
    }
]

# Basic auth check
def check_auth(username, password):
    return username == "admin" and password == "admin123!"

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                'Authentication required\n',
                401,
                {'WWW-Authenticate': 'Basic realm="WAPI"'}
            )
        return f(*args, **kwargs)
    return decorated

@app.route('/wapi/v2.12.3/', methods=['GET'])
@requires_auth
def wapi_root():
    """WAPI version info endpoint"""
    return jsonify({
        "supported_objects": ["record:host"],
        "supported_versions": ["2.12.3"],
        "version": "2.12.3"
    })

@app.route('/wapi/v2.12.3/record:host', methods=['GET'])
@requires_auth
def get_host_records():
    """Get host records with optional filtering"""
    name = request.args.get('name')
    max_results = request.args.get('_max_results', type=int, default=1000)
    
    app.logger.info(f"GET /record:host - name={name}, max_results={max_results}")
    
    if name:
        # Filter by name for existence check
        results = [r for r in HOST_RECORDS if r['name'] == name]
    else:
        # Return all (up to max_results)
        results = HOST_RECORDS[:max_results]
    
    return jsonify(results)

@app.route('/wapi/v2.12.3/record:host', methods=['POST'])
@requires_auth
def create_host_record():
    """Create a new host record"""
    data = request.get_json()
    app.logger.info(f"POST /record:host - data={data}")
    
    name = data.get('name')
    ipv4addrs = data.get('ipv4addrs', [])
    
    if not name or not ipv4addrs:
        return jsonify({"Error": "name and ipv4addrs are required"}), 400
    
    # Create new record
    new_ref = f"record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5leGFtcGxlLm5ldw:{name}/default"
    new_record = {
        "_ref": new_ref,
        "name": name,
        "ipv4addrs": ipv4addrs,
        "extattrs": data.get('extattrs', {}),
        "comment": data.get('comment', '')
    }
    
    HOST_RECORDS.append(new_record)
    app.logger.info(f"Created host record: {name}")
    
    return jsonify(new_ref), 201

@app.route('/wapi/v2.12.3/<path:ref>', methods=['PUT'])
@requires_auth
def update_host_record(ref):
    """Update an existing host record"""
    data = request.get_json()
    app.logger.info(f"PUT /{ref} - data={data}")
    
    # Find record by ref
    for i, record in enumerate(HOST_RECORDS):
        if record['_ref'] == ref:
            # Update record
            record.update({
                'name': data.get('name', record['name']),
                'ipv4addrs': data.get('ipv4addrs', record['ipv4addrs']),
                'extattrs': data.get('extattrs', record['extattrs']),
                'comment': data.get('comment', record.get('comment', ''))
            })
            app.logger.info(f"Updated host record: {record['name']}")
            return jsonify(ref)
    
    return jsonify({"Error": "Record not found"}), 404

@app.route('/wapi/v2.12.3/<path:ref>', methods=['DELETE'])
@requires_auth
def delete_host_record(ref):
    """Delete a host record"""
    app.logger.info(f"DELETE /{ref}")
    
    for i, record in enumerate(HOST_RECORDS):
        if record['_ref'] == ref:
            HOST_RECORDS.pop(i)
            app.logger.info(f"Deleted host record: {record['name']}")
            return jsonify(ref)
    
    return jsonify({"Error": "Record not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "records": len(HOST_RECORDS)})

if __name__ == '__main__':
    print("=" * 60)
    print("Mock Infoblox WAPI Server")
    print("=" * 60)
    print(f"Listening on: https://0.0.0.0:443")
    print(f"Username: admin")
    print(f"Password: admin123!")
    print(f"Test records: {len(HOST_RECORDS)}")
    print("=" * 60)
    
    # Run with SSL
    app.run(host='0.0.0.0', port=443, ssl_context='adhoc')
