#!/usr/bin/env python3
import argparse
import os
import requests
import sys
import time
import json
import re
from datetime import datetime

def get_service_id(api_key, service_name):
    """Get the service ID from the service name"""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(
        "https://api.render.com/v1/services",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error fetching services: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    services_data = response.json()
    
    # Debug: print structure of the response if verbose mode
    if os.environ.get('RENDER_VERBOSE', '0') == '1':
        print("API Response structure:")
        print(json.dumps(services_data, indent=2)[:500] + "..." if len(json.dumps(services_data)) > 500 else json.dumps(services_data, indent=2))
    else:
        print("Fetching service information...")
    
    # Handle nested service objects
    if isinstance(services_data, list):
        for item in services_data:
            # Check if this is the format with nested service object
            if isinstance(item, dict) and "service" in item and isinstance(item["service"], dict):
                service = item["service"]
                if "name" in service and service["name"] == service_name:
                    if "id" in service:
                        print(f"Found service {service_name} with ID {service['id']}")
                        return service["id"]
    
    print(f"Service {service_name} not found in the response. Please check the service name.")
    return None

def fetch_logs(api_key, service_id, limit=100, cursor=None):
    """Fetch logs for a service"""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    
    # Try different API endpoints for logs
    urls = [
        f"https://api.render.com/v1/services/{service_id}/events",  # Let's try this one first as it was successful
        f"https://api.render.com/v1/services/{service_id}/logs",
        f"https://api.render.com/v1/web/{service_id}/logs",
        f"https://api.render.com/v1/web/services/{service_id}/logs",
        f"https://api.render.com/v1/web-services/{service_id}/logs"
    ]
    
    success = False
    logs_data = None
    
    for url in urls:
        if os.environ.get('RENDER_VERBOSE', '0') == '1':
            print(f"Trying to fetch logs from: {url}")
        else:
            print(f"Fetching logs...")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                logs_data = response.json()
                # Debug: print structure of the logs response if verbose mode
                if os.environ.get('RENDER_VERBOSE', '0') == '1':
                    print("Success! Logs API Response structure:")
                    print(json.dumps(logs_data, indent=2)[:500] + "..." if len(json.dumps(logs_data)) > 500 else json.dumps(logs_data, indent=2))
                else:
                    print("Successfully fetched logs.")
                success = True
                break
            else:
                if os.environ.get('RENDER_VERBOSE', '0') == '1':
                    print(f"Endpoint {url} returned status {response.status_code}")
        except Exception as e:
            if os.environ.get('RENDER_VERBOSE', '0') == '1':
                print(f"Error accessing {url}: {e}")
    
    if not success:
        print("Failed to fetch logs from any of the endpoints.")
        sys.exit(1)
    
    return logs_data

def extract_logs_from_response(logs_data):
    """Extract logs from the API response, which could be in various formats"""
    logs = []
    
    # If logs_data is a list, it might be a list of log entries or event entries
    if isinstance(logs_data, list):
        for item in logs_data:
            if isinstance(item, dict):
                # Handle case where each item has an "event" field (like in /events endpoint)
                if "event" in item and isinstance(item["event"], dict):
                    event = item["event"]
                    log_entry = {
                        "id": event.get("id", ""),
                        "timestamp": event.get("timestamp", ""),
                        "type": event.get("type", ""),
                        "details": event.get("details", {})
                    }
                    logs.append(log_entry)
                else:
                    # It's probably a direct log entry
                    logs.append(item)
    # If logs_data is a dict, look for logs under common keys
    elif isinstance(logs_data, dict):
        for key in ["logs", "events", "data", "items"]:
            if key in logs_data and isinstance(logs_data[key], list):
                logs = logs_data[key]
                break
    
    return logs

def format_log_entry(log, colorize=False, show_timestamp=True):
    """Format a log entry for display"""
    # Try to extract timestamp
    timestamp = None
    for ts_field in ["timestamp", "time", "created_at", "createdAt", "date"]:
        if ts_field in log:
            timestamp = log[ts_field]
            break
    
    # Format the timestamp if present
    formatted_timestamp = ""
    if timestamp and show_timestamp:
        try:
            # Try to parse ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            # If parsing fails, use the original timestamp
            formatted_timestamp = timestamp
    
    # Try to extract message
    message = ""
    # First check if this is an event with details
    if "type" in log:
        event_type = log.get("type", "")
        details = log.get("details", {})
        if isinstance(details, dict):
            # Format depending on event type
            if event_type == "deploy_ended":
                status = details.get("deployStatus", "unknown")
                if colorize:
                    if status == "succeeded":
                        status_str = "\033[32m" + status + "\033[0m"  # Green for success
                    elif status == "failed":
                        status_str = "\033[31m" + status + "\033[0m"  # Red for failure
                    else:
                        status_str = status
                else:
                    status_str = status
                message = f"Deployment {status_str}"
            elif event_type == "build_ended":
                status = details.get("buildStatus", "unknown")
                if colorize:
                    if status == "succeeded":
                        status_str = "\033[32m" + status + "\033[0m"  # Green for success
                    elif status == "failed":
                        status_str = "\033[31m" + status + "\033[0m"  # Red for failure
                    else:
                        status_str = status
                else:
                    status_str = status
                message = f"Build {status_str}"
            else:
                message = f"Event: {event_type}"
                if details:
                    message += f" - {format_details(details)}"
        else:
            message = f"Event: {event_type}"
    else:
        # Try common message field names
        for msg_field in ["message", "text", "content", "log", "line"]:
            if msg_field in log:
                message = log[msg_field]
                break
        
        # If still no message, just dump the whole log entry
        if not message:
            # Remove some fields to make it more readable
            log_copy = log.copy()
            for field in ["id", "timestamp", "time", "created_at", "createdAt", "date"]:
                if field in log_copy:
                    del log_copy[field]
            message = json.dumps(log_copy)
    
    if show_timestamp:
        return f"{formatted_timestamp} {message}"
    else:
        return message

def format_details(details):
    """Format event details more concisely"""
    if not details or not isinstance(details, dict):
        return str(details)
    
    # Format specific known fields
    result = {}
    # Keep certain fields and format them
    for key in details:
        if key in ['buildId', 'deployId', 'deployStatus', 'buildStatus']:
            result[key] = details[key]
        elif key == 'trigger' and isinstance(details[key], dict):
            # Just extract the most useful info from trigger
            trigger = details[key]
            trigger_info = {}
            for k in ['manual', 'clearCache', 'firstBuild', 'newCommit']:
                if k in trigger:
                    trigger_info[k] = trigger[k]
            if trigger_info:
                result['trigger'] = trigger_info
    
    return json.dumps(result)

def main():
    parser = argparse.ArgumentParser(description="Fetch logs from Render")
    parser.add_argument("--service-name", required=True, help="Name of the service")
    parser.add_argument("--api-key", help="Render API key")
    parser.add_argument("--limit", type=int, default=100, help="Number of log lines to fetch")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs in real-time")
    parser.add_argument("--filter", help="Filter logs containing this string (case insensitive)")
    parser.add_argument("--output", "-o", help="Output file to write logs to")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed API responses")
    parser.add_argument("--no-color", action="store_true", help="Disable colorized output")
    parser.add_argument("--errors-only", action="store_true", help="Show only error events")
    parser.add_argument("--no-timestamp", action="store_true", help="Hide timestamps in output")
    
    args = parser.parse_args()
    
    # Set verbose mode if requested
    if args.verbose:
        os.environ['RENDER_VERBOSE'] = '1'
    
    # Get API key from arguments or environment
    api_key = args.api_key or os.environ.get("RENDER_API_KEY")
    if not api_key:
        print("Error: No API key provided. Use --api-key or set RENDER_API_KEY environment variable")
        sys.exit(1)
    
    # Get service ID from service name
    service_id = get_service_id(api_key, args.service_name)
    if not service_id:
        sys.exit(1)
    
    print(f"Found service ID: {service_id}")
    
    # Compile filter regex if specified
    filter_regex = None
    if args.filter:
        try:
            filter_regex = re.compile(args.filter, re.IGNORECASE)
            print(f"Filtering logs containing: {args.filter}")
        except re.error:
            print(f"Warning: Invalid regex pattern '{args.filter}'. Will use as plain text.")
            filter_regex = re.compile(re.escape(args.filter), re.IGNORECASE)
    
    # Fetch logs
    if args.follow:
        # For following logs, get recent logs first then poll for new ones
        print(f"Following logs for {args.service_name}...")
        last_log_id = None
        output_file = open(args.output, "a") if args.output else None
        
        try:
            while True:
                logs_data = fetch_logs(api_key, service_id, args.limit)
                logs = extract_logs_from_response(logs_data)
                
                # If we have a last log ID, only show newer logs
                if last_log_id:
                    new_logs = []
                    for log in logs:
                        if log.get("id", "") > last_log_id:
                            new_logs.append(log)
                    logs = new_logs
                
                # Update last log ID if we have logs with IDs
                if logs and "id" in logs[0]:
                    last_log_id = logs[0]["id"]
                
                # Display logs
                for log in reversed(logs):
                    try:
                        # Skip non-error events if errors-only is specified
                        if args.errors_only:
                            if "type" in log and "details" in log:
                                details = log.get("details", {})
                                if isinstance(details, dict):
                                    status = details.get("deployStatus", "")
                                    build_status = details.get("buildStatus", "")
                                    if status != "failed" and build_status != "failed":
                                        continue
                        
                        log_line = format_log_entry(log, colorize=not args.no_color, show_timestamp=not args.no_timestamp)
                        
                        # Apply filter if specified
                        if filter_regex and not filter_regex.search(log_line):
                            continue
                            
                        print(log_line)
                        if output_file:
                            # Write without color codes to file
                            output_file.write(format_log_entry(log, colorize=False, show_timestamp=not args.no_timestamp) + "\n")
                            output_file.flush()
                    except Exception as e:
                        print(f"Error processing log: {e}")
                        if args.verbose:
                            print(f"Log entry: {log}")
                
                time.sleep(2)  # Poll every 2 seconds
                
        except KeyboardInterrupt:
            print("\nStopping log follow...")
            if output_file:
                output_file.close()
    else:
        # For one-time fetch
        logs_data = fetch_logs(api_key, service_id, args.limit)
        logs = extract_logs_from_response(logs_data)
        
        if not logs:
            print("No logs found in the response.")
            sys.exit(0)
            
        print(f"Found {len(logs)} log entries.")
        
        # Filter logs if needed
        if args.errors_only:
            filtered_logs = []
            for log in logs:
                if "type" in log and "details" in log:
                    details = log.get("details", {})
                    if isinstance(details, dict):
                        status = details.get("deployStatus", "")
                        build_status = details.get("buildStatus", "")
                        if status == "failed" or build_status == "failed":
                            filtered_logs.append(log)
            logs = filtered_logs
            print(f"Showing {len(logs)} error events.")
        
        if args.output:
            with open(args.output, "w") as f:
                for log in reversed(logs):
                    try:
                        log_line = format_log_entry(log, colorize=False, show_timestamp=not args.no_timestamp)
                        
                        # Apply filter if specified
                        if filter_regex and not filter_regex.search(log_line):
                            continue
                            
                        f.write(log_line + "\n")
                    except Exception as e:
                        f.write(f"Error processing log: {e}\n")
                        if args.verbose:
                            f.write(f"Log entry: {log}\n")
            print(f"Logs written to {args.output}")
        else:
            displayed_count = 0
            for log in reversed(logs):
                try:
                    log_line = format_log_entry(log, colorize=not args.no_color, show_timestamp=not args.no_timestamp)
                    
                    # Apply filter if specified
                    if filter_regex and not filter_regex.search(log_line):
                        continue
                        
                    print(log_line)
                    displayed_count += 1
                except Exception as e:
                    print(f"Error processing log entry: {e}")
                    if args.verbose:
                        print(f"Log entry: {log}")
            
            if filter_regex and displayed_count == 0:
                print(f"No logs found matching filter: {args.filter}")

if __name__ == "__main__":
    main() 