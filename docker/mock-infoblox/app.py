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

NETWORK_VIEWS = [
    {
        "_ref": "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:default/true",
        "name": "default",
        "is_default": True,
        "comment": "Default network view"
    }
]

IPV4_NETWORKS = [
    {
        "_ref": "network/ZG5zLm5ldHdvcmskMTkyLjE2OC4xLjAvMjQvMA:192.168.1.0/24/default",
        "network": "192.168.1.0/24",
        "network_view": "default",
        "comment": "Lab network 1",
        "extattrs": {"Department": {"value": "IT"}}
    },
    {
        "_ref": "network/ZG5zLm5ldHdvcmskMTkyLjE2OC4yLjAvMjQvMA:192.168.2.0/24/default",
        "network": "192.168.2.0/24",
        "network_view": "default",
        "comment": "Lab network 2",
        "extattrs": {"Department": {"value": "Operations"}}
    },
    {
        "_ref": "network/ZG5zLm5ldHdvcmskMTAuMTAwLjAuMC8xNC8w:10.100.0.0/14/default",
        "network": "10.100.0.0/14",
        "network_view": "default",
        "comment": "Production network",
        "extattrs": {"Environment": {"value": "Production"}}
    }
]

IPV4_NETWORK_CONTAINERS = [
    {
        "_ref": "networkcontainer/ZG5zLm5ldHdvcmtfY29udGFpbmVyJDEwLjAuMC4wLzgvMA:10.0.0.0/8/default",
        "network": "10.0.0.0/8",
        "network_view": "default",
        "comment": "Private network container",
        "extattrs": {"Type": {"value": "Private"}}
    },
    {
        "_ref": "networkcontainer/ZG5zLm5ldHdvcmtfY29udGFpbmVyJDE5Mi4xNjguMC4wLzE2LzA:192.168.0.0/16/default",
        "network": "192.168.0.0/16",
        "network_view": "default",
        "comment": "Lab network container",
        "extattrs": {"Type": {"value": "Lab"}}
    }
]

FIXED_ADDRESSES = [
    {
        "_ref": "fixedaddress/ZG5zLmZpeGVkX2FkZHJlc3MkMTkyLjE2OC4xLjEwMC4w:192.168.1.100/default",
        "ipv4addr": "192.168.1.100",
        "network": "192.168.1.0/24",
        "network_view": "default",
        "mac": "00:11:22:33:44:55",
        "comment": "Printer 1",
        "extattrs": {"DeviceType": {"value": "Printer"}}
    },
    {
        "_ref": "fixedaddress/ZG5zLmZpeGVkX2FkZHJlc3MkMTkyLjE2OC4yLjEwMC4w:192.168.2.100/default",
        "ipv4addr": "192.168.2.100",
        "network": "192.168.2.0/24",
        "network_view": "default",
        "mac": "00:11:22:33:44:66",
        "comment": "Access Point 1",
        "extattrs": {"DeviceType": {"value": "WiFi AP"}}
    }
]

IPV4_RANGES = [
    {
        "_ref": "range/ZG5zLnJhbmdlJDE5Mi4xNjguMS4yMDAuMTkyLjE2OC4xLjI1MC4w:192.168.1.200/192.168.1.250/default",
        "start_addr": "192.168.1.200",
        "end_addr": "192.168.1.250",
        "network": "192.168.1.0/24",
        "network_view": "default",
        "comment": "DHCP range for lab devices",
        "extattrs": {"Purpose": {"value": "DHCP"}}
    }
]

ALIAS_RECORDS = [
    {
        "_ref": "record:cname/ZG5zLmNuYW1lJHd3dy5leGFtcGxlLmNvbS4w:www.example.com/default",
        "name": "www.example.com",
        "canonical": "server1.example.com",
        "zone": "example.com",
        "comment": "Web server alias"
    }
]

IPV4_SHARED_NETWORKS = [
    {
        "_ref": "sharednetwork/ZG5zLnNoYXJlZF9uZXR3b3JrJGRlZmF1bHQuc2hhcmVkLW5ldC0x:shared-net-1/default",
        "name": "shared-net-1",
        "network_view": "default",
        "networks": ["192.168.1.0/24", "192.168.2.0/24"],
        "comment": "Shared lab networks"
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

@app.route('/wapi/v2.12.3/networkview', methods=['GET'])
@requires_auth
def get_network_views():
    """Get network views"""
    return jsonify(NETWORK_VIEWS)

@app.route('/wapi/v2.12.3/network', methods=['GET', 'POST'])
@requires_auth
def networks():
    """Get or create IPv4 networks"""
    if request.method == 'POST':
        # Create new network
        data = request.get_json()
        network_cidr = data.get('network')
        comment = data.get('comment', '')
        network_view = data.get('network_view', 'default')
        
        # Check if network already exists
        if any(n['network'] == network_cidr for n in IPV4_NETWORKS):
            return jsonify({
                "Error": "AdmConDataError: None (IBDataConflictError: IB.Data.Conflict:The network already exists.)",
                "code": "Client.Ibap.Data.Conflict",
                "text": "The network already exists."
            }), 400
        
        # Create network reference
        import base64
        ref_data = f"network${network_cidr}/{network_view}"
        ref_b64 = base64.b64encode(ref_data.encode()).decode()
        ref = f"network/{ref_b64}:{network_cidr}/{network_view}"
        
        # Add to networks list
        new_network = {
            "_ref": ref,
            "network": network_cidr,
            "network_view": network_view,
            "comment": comment,
            "extattrs": {}
        }
        IPV4_NETWORKS.append(new_network)
        
        # Return just the ref (standard Infoblox behavior)
        return jsonify(ref), 201
    else:
        # GET - return all networks
        return jsonify(IPV4_NETWORKS)

@app.route('/wapi/v2.12.3/networkcontainer', methods=['GET'])
@requires_auth
def get_network_containers():
    """Get IPv4 network containers"""
    return jsonify(IPV4_NETWORK_CONTAINERS)

@app.route('/wapi/v2.12.3/fixedaddress', methods=['GET'])
@requires_auth
def get_fixed_addresses():
    """Get IPv4 fixed addresses"""
    return jsonify(FIXED_ADDRESSES)

@app.route('/wapi/v2.12.3/range', methods=['GET'])
@requires_auth
def get_ranges():
    """Get IPv4 ranges"""
    return jsonify(IPV4_RANGES)

@app.route('/wapi/v2.12.3/record:cname', methods=['GET'])
@requires_auth
def get_cname_records():
    """Get CNAME (alias) records"""
    return jsonify(ALIAS_RECORDS)

@app.route('/wapi/v2.12.3/sharednetwork', methods=['GET'])
@requires_auth
def get_shared_networks():
    """Get IPv4 shared networks"""
    return jsonify(IPV4_SHARED_NETWORKS)

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
