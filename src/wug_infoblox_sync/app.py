from __future__ import annotations

import logging
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

from .config import load_settings
from .sync_service import SyncService
from .wug_client import WUGClient
from .infoblox_client import InfobloxClient
from .models import InfobloxHostRecord
from . import ip_utils


def create_app() -> Flask:
    load_dotenv()
    settings = load_settings()

    logging.basicConfig(level=getattr(logging, settings.sync_log_level.upper(), logging.INFO))

    app = Flask(__name__)
    service = SyncService(settings)
    wug_client = WUGClient(settings)
    infoblox_client = InfobloxClient(settings)

    @app.get("/")
    def index():
        """Dashboard UI"""
        return render_template("index.html")

    @app.get("/api")
    def api_info() -> tuple:
        return jsonify({
            "service": "wug-infoblox-sync",
            "version": "1.0.0",
            "endpoints": {
                "GET /status": "Health check",
                "POST /sync": "Sync WUG devices to Infoblox (payload: {limit?: number})",
                "POST /dry-run": "Dry run WUG to Infoblox sync (payload: {limit?: number})",
                "POST /reverse-sync": "Sync Infoblox host records to WUG (payload: {limit?: number})",
                "POST /reverse-dry-run": "Dry run Infoblox to WUG sync (payload: {limit?: number})",
                "POST /add-test-device": "Add test device to WUG (payload: {display_name, ip_address, hostname?})",
                "POST /add-test-host": "Add test host record to Infoblox and WUG (payload: {hostname, ip_address, comment?, enable_monitoring?})",
                "GET /wug-devices": "Get all devices from WUG",
                "GET /infoblox-hosts": "Get all host records from Infoblox",
                "DELETE /infoblox-hosts/<hostname>": "Delete a host record from Infoblox",
                "GET /infoblox/network-views": "Get all network views from Infoblox",
                "GET /infoblox/networks": "Get all IPv4 networks from Infoblox",
                "GET /infoblox/networks-with-utilization": "Get all networks with IP utilization and allocated IPs",
                "POST /infoblox/network": "Create new network block (payload: {network: '192.168.10.0/24', comment?: 'description'})",
                "GET /infoblox/network-containers": "Get all IPv4 network containers from Infoblox",
                "GET /infoblox/fixed-addresses": "Get all IPv4 fixed addresses from Infoblox",
                "GET /infoblox/ranges": "Get all IPv4 DHCP ranges from Infoblox",
                "GET /infoblox/alias-records": "Get all alias (CNAME) records from Infoblox",
                "GET /infoblox/shared-networks": "Get all IPv4 shared networks from Infoblox",
                "GET /infoblox/networks/<ref>/utilization": "Get IP utilization for network (query: ?network=192.168.1.0/24)",
                "GET /infoblox/networks/<ref>/available-ips": "Get available IPs in network (query: ?network=192.168.1.0/24&limit=100)",
                "GET /infoblox/networks/<ref>/next-available-ip": "Get next available IP in network (query: ?network=192.168.1.0/24)",
                "POST /wug/device": "Create device in WUG (payload: {display_name, ip_address, hostname?, enable_monitoring?})",
                "POST /combined/add-device": "Add device to Infoblox and optionally WUG (payload: {hostname, ip_address, network?, add_to_wug?, enable_monitoring?})"
            }
        }), 200

    @app.get("/status")
    def status() -> tuple:
        return jsonify({"service": "wug-infoblox-sync", "status": "ok"}), 200

    @app.get("/wug-devices")
    def get_wug_devices() -> tuple:
        """Get all devices from WUG"""
        try:
            limit = request.args.get("limit", type=int)
            devices = wug_client.get_devices(limit=limit)
            
            # Format devices for display
            device_list = []
            for device in devices:
                device_list.append({
                    "id": device.get("id"),
                    "name": device.get("displayName", device.get("name", "Unknown")),
                    "ip_address": device.get("primaryAddress", device.get("ipAddress", "N/A")),
                    "hostname": device.get("networkName", device.get("hostname", "N/A")),
                    "device_type": device.get("deviceType", "Unknown"),
                    "status": device.get("isUp", "Unknown")
                })
            
            return jsonify({
                "success": True,
                "count": len(device_list),
                "devices": device_list
            }), 200
            
        except Exception as e:
            logging.exception("Error fetching WUG devices")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch devices from WUG"
            }), 500

    @app.get("/infoblox-hosts")
    def get_infoblox_hosts() -> tuple:
        """Get all host records from Infoblox"""
        try:
            limit = request.args.get("limit", type=int, default=1000)
            hosts = infoblox_client.get_all_host_records(limit=limit)
            
            # Format hosts for display
            # Note: get_all_host_records() transforms the API response:
            # - "name" becomes "hostname"  
            # - "ipv4addrs" becomes "ip_address"
            host_list = []
            for host in hosts:
                host_list.append({
                    "name": host.get("hostname", "Unknown"),
                    "ip_address": host.get("ip_address", "N/A"),
                    "comment": host.get("comment", ""),
                    "extattrs": host.get("extattrs", {})
                })
            
            return jsonify({
                "success": True,
                "count": len(host_list),
                "hosts": host_list
            }), 200
            
        except Exception as e:
            logging.exception("Error fetching Infoblox hosts")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch host records from Infoblox"
            }), 500

    @app.delete("/infoblox-hosts/<hostname>")
    def delete_infoblox_host(hostname: str) -> tuple:
        """Delete a host record from Infoblox"""
        try:
            result = infoblox_client.delete_host_record(hostname)
            
            if result.get("success"):
                return jsonify({
                    "success": True,
                    "message": result.get("message"),
                    "hostname": hostname
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result.get("message"),
                    "hostname": hostname
                }), 404
                
        except Exception as e:
            logging.exception(f"Error deleting host {hostname}")
            return jsonify({
                "success": False,
                "error": str(e),
                "message": f"Failed to delete host record '{hostname}'"
            }), 500

    @app.get("/infoblox/network-views")
    def get_network_views() -> tuple:
        """Get all network views from Infoblox"""
        try:
            views = infoblox_client.get_network_views()
            return jsonify({
                "success": True,
                "count": len(views),
                "network_views": views
            }), 200
        except Exception as e:
            logging.exception("Error fetching network views")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch network views from Infoblox"
            }), 500

    @app.get("/infoblox/networks")
    def get_networks() -> tuple:
        """Get all IPv4 networks from Infoblox"""
        try:
            networks = infoblox_client.get_ipv4_networks()
            return jsonify({
                "success": True,
                "count": len(networks),
                "networks": networks
            }), 200
        except Exception as e:
            logging.exception("Error fetching networks")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch networks from Infoblox"
            }), 500

    @app.get("/infoblox/networks-with-utilization")
    def get_networks_with_utilization() -> tuple:
        """Get all IPv4 networks from Infoblox with IP utilization data"""
        try:
            # Get all networks
            networks = infoblox_client.get_ipv4_networks()
            
            # Get all used IPs
            host_records = infoblox_client.get_all_host_records()
            fixed_addresses = infoblox_client.get_fixed_addresses()
            
            # Build map of all used IPs
            all_used_ips = []
            
            # Extract IPs from host records
            for record in host_records:
                if "ipv4addrs" in record:
                    for ipv4 in record["ipv4addrs"]:
                        if "ipv4addr" in ipv4:
                            all_used_ips.append(ipv4["ipv4addr"])
            
            # Extract IPs from fixed addresses
            for fixed in fixed_addresses:
                if "ipv4addr" in fixed:
                    all_used_ips.append(fixed["ipv4addr"])
            
            # Calculate utilization for each network
            networks_with_util = []
            for network in networks:
                network_cidr = network.get("network")
                if network_cidr and ip_utils.validate_network(network_cidr):
                    # Filter used IPs to those in this network
                    network_used_ips = [
                        ip for ip in all_used_ips 
                        if ip_utils.ip_in_network(ip, network_cidr)
                    ]
                    
                    # Calculate utilization
                    utilization = ip_utils.calculate_utilization(network_cidr, network_used_ips)
                    
                    # Combine network info with utilization
                    network_with_util = {
                        **network,
                        "utilization": {
                            "total_ips": utilization["total_ips"],
                            "used_ips": utilization["used_ips"],
                            "available_ips": utilization["available_ips"],
                            "utilization_percent": utilization["utilization_percent"]
                        },
                        "allocated_ips": network_used_ips  # List of IPs in use
                    }
                    networks_with_util.append(network_with_util)
                else:
                    # Network without valid CIDR, add without utilization
                    networks_with_util.append(network)
            
            return jsonify({
                "success": True,
                "count": len(networks_with_util),
                "networks": networks_with_util
            }), 200
            
        except Exception as e:
            logging.exception("Error fetching networks with utilization")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch networks with utilization from Infoblox"
            }), 500

    @app.post("/infoblox/network")
    def create_network() -> tuple:
        """Create a new IPv4 network in Infoblox"""
        try:
            payload = request.get_json(silent=True) or {}
            network = payload.get("network")
            comment = payload.get("comment", "")
            
            if not network:
                return jsonify({
                    "success": False,
                    "error": "Missing required field",
                    "message": "network field is required (e.g., '192.168.10.0/24')"
                }), 400
            
            # Validate network CIDR
            if not ip_utils.validate_network(network):
                return jsonify({
                    "success": False,
                    "error": "Invalid network CIDR",
                    "message": "Network must be in valid CIDR notation (e.g., '192.168.10.0/24')"
                }), 400
            
            result = infoblox_client.create_network(
                network_cidr=network,
                comment=comment
            )
            
            return jsonify(result), 201
            
        except Exception as e:
            logging.exception("Error creating network")
            error_msg = str(e)
            # Check for duplicate network error
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "Network already exists",
                    "message": f"Network {payload.get('network')} already exists in Infoblox"
                }), 409
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "Failed to create network in Infoblox"
            }), 500

    @app.get("/infoblox/network-containers")
    def get_network_containers() -> tuple:
        """Get all IPv4 network containers from Infoblox"""
        try:
            containers = infoblox_client.get_ipv4_network_containers()
            return jsonify({
                "success": True,
                "count": len(containers),
                "network_containers": containers
            }), 200
        except Exception as e:
            logging.exception("Error fetching network containers")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch network containers from Infoblox"
            }), 500

    @app.get("/infoblox/fixed-addresses")
    def get_fixed_addresses() -> tuple:
        """Get all IPv4 fixed addresses from Infoblox"""
        try:
            addresses = infoblox_client.get_fixed_addresses()
            return jsonify({
                "success": True,
                "count": len(addresses),
                "fixed_addresses": addresses
            }), 200
        except Exception as e:
            logging.exception("Error fetching fixed addresses")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch fixed addresses from Infoblox"
            }), 500

    @app.get("/infoblox/ranges")
    def get_ranges() -> tuple:
        """Get all IPv4 ranges from Infoblox"""
        try:
            ranges = infoblox_client.get_ipv4_ranges()
            return jsonify({
                "success": True,
                "count": len(ranges),
                "ranges": ranges
            }), 200
        except Exception as e:
            logging.exception("Error fetching ranges")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch ranges from Infoblox"
            }), 500

    @app.get("/infoblox/alias-records")
    def get_alias_records() -> tuple:
        """Get all alias (CNAME) records from Infoblox"""
        try:
            aliases = infoblox_client.get_alias_records()
            return jsonify({
                "success": True,
                "count": len(aliases),
                "alias_records": aliases
            }), 200
        except Exception as e:
            logging.exception("Error fetching alias records")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch alias records from Infoblox"
            }), 500

    @app.get("/infoblox/shared-networks")
    def get_shared_networks() -> tuple:
        """Get all IPv4 shared networks from Infoblox"""
        try:
            shared_nets = infoblox_client.get_ipv4_shared_networks()
            return jsonify({
                "success": True,
                "count": len(shared_nets),
                "shared_networks": shared_nets
            }), 200
        except Exception as e:
            logging.exception("Error fetching shared networks")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch shared networks from Infoblox"
            }), 500

    @app.post("/add-test-device")
    def add_test_device() -> tuple:
        """Add a test device to WUG"""
        payload = request.get_json(silent=True) or {}
        display_name = payload.get("display_name")
        ip_address = payload.get("ip_address")
        hostname = payload.get("hostname", ip_address)

        if not display_name or not ip_address:
            return jsonify({"error": "display_name and ip_address are required"}), 400

        try:
            # Check if device already exists
            if wug_client.device_exists(ip_address):
                return jsonify({
                    "error": f"Device with IP {ip_address} already exists in WUG",
                    "ip_address": ip_address
                }), 409

            # Add device to WUG
            result = wug_client.create_device(
                display_name=display_name,
                ip_address=ip_address,
                hostname=hostname,
                device_type="Windows",
                primary_role="Server",
                poll_interval=300
            )
            
            return jsonify({
                "success": True,
                "message": f"Device '{display_name}' added to WUG",
                "device": {
                    "display_name": display_name,
                    "ip_address": ip_address,
                    "hostname": hostname
                },
                "wug_response": result
            }), 201

        except Exception as e:
            logging.exception("Error adding test device")
            return jsonify({
                "error": str(e),
                "message": "Failed to add device to WUG"
            }), 500

    @app.post("/add-test-host")
    def add_test_host() -> tuple:
        """Add a test host record to Infoblox and device to WUG"""
        payload = request.get_json(silent=True) or {}
        hostname = payload.get("hostname")
        ip_address = payload.get("ip_address")
        comment = payload.get("comment", "")
        enable_monitoring = payload.get("enable_monitoring", True)

        if not hostname or not ip_address:
            return jsonify({"error": "hostname and ip_address are required"}), 400

        infoblox_result = None
        wug_result = None
        
        try:
            # Create InfobloxHostRecord object
            extattrs = {
                "Source": {"value": "Manual"},
                "Created": {"value": "Dashboard"}
            }
            if comment:
                extattrs["Comment"] = {"value": comment}
            
            host_record = InfobloxHostRecord(
                fqdn=hostname,
                ip_address=ip_address,
                network_view="default",
                extattrs=extattrs
            )
            
            # Add host record to Infoblox
            infoblox_result = infoblox_client.upsert_host_record(
                record=host_record,
                dry_run=False
            )
            
        except Exception as e:
            logging.exception("Error adding host to Infoblox")
            return jsonify({
                "error": str(e),
                "message": "Failed to add host record to Infoblox"
            }), 500
        
        # Try to add device to WUG (don't fail if this times out)
        try:
            if wug_client.device_exists(ip_address):
                wug_result = {
                    "success": False,
                    "message": f"Device with IP {ip_address} already exists in WUG",
                    "skipped": True
                }
            else:
                wug_result = wug_client.create_device(
                    display_name=hostname,
                    ip_address=ip_address,
                    hostname=hostname,
                    device_type="Network Device",
                    primary_role="Device",
                    poll_interval=300,
                    enable_monitoring=enable_monitoring
                )
        except Exception as e:
            logging.exception("Error adding device to WUG")
            wug_result = {
                "success": False,
                "message": f"WUG operation failed or timed out: {str(e)}",
                "error": True
            }
        
        # Build response
        message = f"Host '{hostname}' added to Infoblox"
        warning = None
        
        if wug_result and wug_result.get("success"):
            message += " and WUG"
        elif wug_result and wug_result.get("skipped"):
            message += " (device already in WUG)"
        elif wug_result and wug_result.get("error"):
            message += " (WUG operation failed)"
        elif wug_result and not wug_result.get("success"):
            # Check for license error
            wug_msg = wug_result.get("message", "")
            if "License" in wug_msg or "maximum devices" in wug_msg:
                warning = "⚠️ WUG License Limit: Cannot add more devices. Please remove unused devices or upgrade license."
                message += " (WUG license limit reached)"
            elif wug_result.get("errors"):
                error_msgs = wug_result.get("errors", [])
                if error_msgs:
                    first_error = error_msgs[0].get("messages", ["Unknown error"])[0] if isinstance(error_msgs, list) else str(error_msgs)
                    warning = f"⚠️ WUG Error: {first_error}"
                message += " (WUG error - see details)"
            else:
                message += " (WUG operation failed)"
            
        return jsonify({
            "success": True,
            "message": message,
            "warning": warning,
            "host": {
                "hostname": hostname,
                "ip_address": ip_address,
                "comment": comment,
                "monitoring_enabled": enable_monitoring
            },
            "infoblox_response": infoblox_result,
            "wug_response": wug_result
        }), 201

    @app.post("/sync")
    def sync() -> tuple:
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_sync(dry_run=False, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    @app.post("/dry-run")
    def dry_run() -> tuple:
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_sync(dry_run=True, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    @app.post("/reverse-sync")
    def reverse_sync() -> tuple:
        """Import devices from Infoblox into WhatsUp Gold"""
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_reverse_sync(dry_run=False, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    @app.post("/reverse-dry-run")
    def reverse_dry_run() -> tuple:
        """Dry run of importing devices from Infoblox into WhatsUp Gold"""
        payload = request.get_json(silent=True) or {}
        limit = payload.get("limit")
        result = service.run_reverse_sync(dry_run=True, limit=limit)
        return jsonify(SyncService.result_dict(result)), 200

    # IP Space Management Endpoints
    
    @app.get("/infoblox/networks/<network_ref>/utilization")
    def get_network_utilization(network_ref: str) -> tuple:
        """
        Get IP utilization statistics for a specific network.
        Query params:
          - network: CIDR notation (e.g., 192.168.1.0/24)
        """
        try:
            # Get network CIDR from query params or decode from ref
            network_cidr = request.args.get("network")
            if not network_cidr:
                return jsonify({
                    "error": "Missing 'network' query parameter",
                    "message": "Please provide network in CIDR notation (e.g., ?network=192.168.1.0/24)"
                }), 400
            
            if not ip_utils.validate_network(network_cidr):
                return jsonify({
                    "error": "Invalid network CIDR",
                    "message": "Network must be in CIDR notation (e.g., 192.168.1.0/24)"
                }), 400
            
            # Get all used IPs from Infoblox for this network
            host_records = infoblox_client.get_all_host_records()
            fixed_addresses = infoblox_client.get_fixed_addresses()
            
            used_ips = []
            
            # Extract IPs from host records
            for record in host_records:
                if "ipv4addrs" in record:
                    for ipv4 in record["ipv4addrs"]:
                        if "ipv4addr" in ipv4:
                            ip = ipv4["ipv4addr"]
                            if ip_utils.ip_in_network(ip, network_cidr):
                                used_ips.append(ip)
            
            # Extract IPs from fixed addresses
            for fixed in fixed_addresses:
                if "ipv4addr" in fixed:
                    ip = fixed["ipv4addr"]
                    if ip_utils.ip_in_network(ip, network_cidr):
                        used_ips.append(ip)
            
            # Calculate utilization
            utilization = ip_utils.calculate_utilization(network_cidr, used_ips)
            
            return jsonify({
                "success": True,
                "utilization": utilization
            }), 200
            
        except Exception as e:
            logging.exception("Error calculating network utilization")
            return jsonify({
                "error": str(e),
                "message": "Failed to calculate network utilization"
            }), 500

    @app.get("/infoblox/networks/<network_ref>/available-ips")
    def get_available_ips(network_ref: str) -> tuple:
        """
        Get list of available IP addresses in a network.
        Query params:
          - network: CIDR notation (e.g., 192.168.1.0/24)
          - limit: Max number of IPs to return (default: 100)
        """
        try:
            network_cidr = request.args.get("network")
            if not network_cidr:
                return jsonify({
                    "error": "Missing 'network' query parameter",
                    "message": "Please provide network in CIDR notation (e.g., ?network=192.168.1.0/24)"
                }), 400
            
            if not ip_utils.validate_network(network_cidr):
                return jsonify({
                    "error": "Invalid network CIDR",
                    "message": "Network must be in CIDR notation (e.g., 192.168.1.0/24)"
                }), 400
            
            limit = request.args.get("limit", type=int, default=100)
            
            # Get all used IPs from Infoblox for this network
            host_records = infoblox_client.get_all_host_records()
            fixed_addresses = infoblox_client.get_fixed_addresses()
            
            used_ips = []
            
            # Extract IPs from host records
            for record in host_records:
                if "ipv4addrs" in record:
                    for ipv4 in record["ipv4addrs"]:
                        if "ipv4addr" in ipv4:
                            ip = ipv4["ipv4addr"]
                            if ip_utils.ip_in_network(ip, network_cidr):
                                used_ips.append(ip)
            
            # Extract IPs from fixed addresses
            for fixed in fixed_addresses:
                if "ipv4addr" in fixed:
                    ip = fixed["ipv4addr"]
                    if ip_utils.ip_in_network(ip, network_cidr):
                        used_ips.append(ip)
            
            # Get available IPs
            available = ip_utils.get_available_ips(network_cidr, used_ips, limit=limit)
            
            return jsonify({
                "success": True,
                "network": network_cidr,
                "count": len(available),
                "available_ips": available
            }), 200
            
        except Exception as e:
            logging.exception("Error fetching available IPs")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch available IPs"
            }), 500

    @app.get("/infoblox/networks/<network_ref>/next-available-ip")
    def get_next_available_ip(network_ref: str) -> tuple:
        """
        Get the next available IP address in a network.
        Query params:
          - network: CIDR notation (e.g., 192.168.1.0/24)
        """
        try:
            network_cidr = request.args.get("network")
            if not network_cidr:
                return jsonify({
                    "error": "Missing 'network' query parameter",
                    "message": "Please provide network in CIDR notation (e.g., ?network=192.168.1.0/24)"
                }), 400
            
            if not ip_utils.validate_network(network_cidr):
                return jsonify({
                    "error": "Invalid network CIDR",
                    "message": "Network must be in CIDR notation (e.g., 192.168.1.0/24)"
                }), 400
            
            # Get all used IPs from Infoblox for this network
            host_records = infoblox_client.get_all_host_records()
            fixed_addresses = infoblox_client.get_fixed_addresses()
            
            used_ips = []
            
            # Extract IPs from host records
            for record in host_records:
                if "ipv4addrs" in record:
                    for ipv4 in record["ipv4addrs"]:
                        if "ipv4addr" in ipv4:
                            ip = ipv4["ipv4addr"]
                            if ip_utils.ip_in_network(ip, network_cidr):
                                used_ips.append(ip)
            
            # Extract IPs from fixed addresses
            for fixed in fixed_addresses:
                if "ipv4addr" in fixed:
                    ip = fixed["ipv4addr"]
                    if ip_utils.ip_in_network(ip, network_cidr):
                        used_ips.append(ip)
            
            # Get next available IP
            next_ip = ip_utils.get_next_available_ip(network_cidr, used_ips)
            
            if next_ip:
                return jsonify({
                    "success": True,
                    "network": network_cidr,
                    "next_available_ip": next_ip
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "network": network_cidr,
                    "message": "No available IPs in this network"
                }), 404
            
        except Exception as e:
            logging.exception("Error fetching next available IP")
            return jsonify({
                "error": str(e),
                "message": "Failed to fetch next available IP"
            }), 500

    # WUG Device Management Endpoints
    
    @app.post("/wug/device")
    def create_wug_device() -> tuple:
        """
        Create a new device in WhatsUp Gold.
        Payload: {
          display_name: string,
          ip_address: string,
          hostname?: string,
          device_type?: string,
          primary_role?: string,
          poll_interval?: number,
          enable_monitoring?: boolean
        }
        """
        try:
            payload = request.get_json(silent=True) or {}
            
            # Validate required fields
            display_name = payload.get("display_name")
            ip_address = payload.get("ip_address")
            
            if not display_name or not ip_address:
                return jsonify({
                    "error": "Missing required fields",
                    "message": "display_name and ip_address are required"
                }), 400
            
            if not ip_utils.validate_ip(ip_address):
                return jsonify({
                    "error": "Invalid IP address",
                    "message": "ip_address must be a valid IPv4 address"
                }), 400
            
            # Check if device already exists
            if wug_client.device_exists(ip_address):
                return jsonify({
                    "success": False,
                    "message": f"Device with IP {ip_address} already exists in WUG"
                }), 409
            
            # Create device in WUG
            result = wug_client.create_device(
                display_name=display_name,
                ip_address=ip_address,
                hostname=payload.get("hostname"),
                device_type=payload.get("device_type", "Network Device"),
                primary_role=payload.get("primary_role", "Device"),
                poll_interval=payload.get("poll_interval", 60),
                enable_monitoring=payload.get("enable_monitoring", True)
            )
            
            if result.get("success"):
                return jsonify(result), 201
            else:
                return jsonify(result), 400
            
        except Exception as e:
            logging.exception("Error creating WUG device")
            return jsonify({
                "error": str(e),
                "message": "Failed to create device in WUG"
            }), 500

    # Combined Workflow Endpoints
    
    @app.post("/combined/add-device")
    def add_device_combined() -> tuple:
        """
        Add device to Infoblox and optionally to WUG in one operation.
        Payload: {
          hostname: string,
          ip_address: string,
          network: string (CIDR notation),
          comment?: string,
          add_to_wug?: boolean (default: false),
          enable_monitoring?: boolean (default: true)
        }
        """
        try:
            payload = request.get_json(silent=True) or {}
            
            # Validate required fields
            hostname = payload.get("hostname")
            ip_address = payload.get("ip_address")
            network_cidr = payload.get("network")
            
            if not hostname or not ip_address:
                return jsonify({
                    "error": "Missing required fields",
                    "message": "hostname and ip_address are required"
                }), 400
            
            if not ip_utils.validate_ip(ip_address):
                return jsonify({
                    "error": "Invalid IP address",
                    "message": "ip_address must be a valid IPv4 address"
                }), 400
            
            # Validate IP is in network if network is provided
            if network_cidr:
                if not ip_utils.validate_network(network_cidr):
                    return jsonify({
                        "error": "Invalid network CIDR",
                        "message": "network must be in CIDR notation (e.g., 192.168.1.0/24)"
                    }), 400
                
                if not ip_utils.ip_in_network(ip_address, network_cidr):
                    return jsonify({
                        "error": "IP not in network",
                        "message": f"IP {ip_address} is not in network {network_cidr}"
                    }), 400
            
            results = {
                "infoblox": None,
                "wug": None
            }
            
            # Add to Infoblox
            try:
                host_record = InfobloxHostRecord(
                    fqdn=hostname,
                    ip_address=ip_address,
                    network_view="default",
                    extattrs={"Comment": {"value": payload.get("comment", f"Added via combined workflow")}}
                )
                
                infoblox_result = infoblox_client.upsert_host_record(host_record, dry_run=False)
                results["infoblox"] = {
                    "success": True,
                    "action": infoblox_result.get("action", "created"),
                    "hostname": hostname,
                    "ip_address": ip_address
                }
            except Exception as e:
                results["infoblox"] = {
                    "success": False,
                    "error": str(e)
                }
                # If Infoblox fails, still try WUG if requested
            
            # Optionally add to WUG
            add_to_wug = payload.get("add_to_wug", False)
            if add_to_wug:
                try:
                    # Check if device already exists
                    if wug_client.device_exists(ip_address):
                        results["wug"] = {
                            "success": False,
                            "message": f"Device with IP {ip_address} already exists in WUG",
                            "skipped": True
                        }
                    else:
                        wug_result = wug_client.create_device(
                            display_name=hostname,
                            ip_address=ip_address,
                            hostname=hostname,
                            enable_monitoring=payload.get("enable_monitoring", True)
                        )
                        results["wug"] = wug_result
                except Exception as e:
                    results["wug"] = {
                        "success": False,
                        "error": str(e)
                    }
            else:
                results["wug"] = {
                    "skipped": True,
                    "message": "WUG creation not requested (add_to_wug=false)"
                }
            
            # Determine overall success
            infoblox_success = results["infoblox"] and results["infoblox"].get("success", False)
            wug_success = (
                not add_to_wug or 
                (results["wug"] and (results["wug"].get("success", False) or results["wug"].get("skipped", False)))
            )
            
            overall_success = infoblox_success and wug_success
            status_code = 201 if overall_success else 207  # 207 = Multi-Status
            
            return jsonify({
                "success": overall_success,
                "results": results
            }), status_code
            
        except Exception as e:
            logging.exception("Error in combined add device")
            return jsonify({
                "error": str(e),
                "message": "Failed to add device"
            }), 500

    return app


def main() -> None:
    app = create_app()
    settings = load_settings()
    app.run(host=settings.flask_host, port=settings.flask_port)


if __name__ == "__main__":
    main()
