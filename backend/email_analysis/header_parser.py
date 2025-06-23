# PhishGard-AI/analysis/header_parser.py

import re
from email.utils import parseaddr

def parse_authentication_results(auth_results_string):
    """Parse une chaîne Authentication-Results ou ARC-Authentication-Results."""
    parsed = {"spf": [], "dkim": [], "dmarc": []}
    if not auth_results_string:
        return parsed

    # SPF
    spf_matches = re.findall(r'spf=([\w-]+)\s*(?:\((.*?)\))?\s*(?:smtp\.mailfrom=([\S]+)|smtp\.helo=([\S]+))?', auth_results_string, re.IGNORECASE)
    for match in spf_matches:
        parsed["spf"].append({
            "result": match[0].lower(),
            "details": match[1].strip() if match[1] else None,
            "mailfrom_or_helo": match[2] or match[3] or None
        })

    # DKIM
    dkim_matches = re.findall(r'dkim=([\w-]+)\s+(?:header\.i=([\S]+))?\s*(?:header\.s=([\S]+))?\s*(?:header\.b=([\S]+))?', auth_results_string, re.IGNORECASE)
    for match in dkim_matches:
        parsed["dkim"].append({
            "result": match[0].lower(),
            "domain": match[1].lstrip('@') if match[1] else None,
            "selector": match[2] if match[2] else None,
        })
    
    # DMARC
    dmarc_matches = re.findall(r'dmarc=([\w-]+)\s*(?:\((.*?)\))?\s*(?:header\.from=([\S]+))?', auth_results_string, re.IGNORECASE)
    for match in dmarc_matches:
        dmarc_details_str = match[1].strip() if match[1] else ""
        policy = re.search(r'p=([\w-]+)', dmarc_details_str, re.IGNORECASE)
        # --- CORRECTION: Ajout de la politique de sous-domaine (sp) ---
        subdomain_policy = re.search(r'sp=([\w-]+)', dmarc_details_str, re.IGNORECASE)
        disposition = re.search(r'dis=([\w-]+)', dmarc_details_str, re.IGNORECASE)
        
        parsed["dmarc"].append({
            "result": match[0].lower(),
            "policy": policy.group(1).lower() if policy else None,
            "subdomain_policy": subdomain_policy.group(1).lower() if subdomain_policy else None, # Ajouté
            "disposition": disposition.group(1).lower() if disposition else None,
            "from_domain": match[2] if match[2] else None,
            "raw_details": dmarc_details_str # Ajouté
        })
    
    if not parsed["spf"] and not parsed["dkim"] and not parsed["dmarc"] and auth_results_string:
         parsed["raw_value"] = auth_results_string

    return parsed

def parse_received_header(received_string):
    """Parse sommairement un en-tête Received."""
    details = {"raw": received_string, "from_host": None, "from_ip": None, "by_host": None, "timestamp": None, "protocol": None}
    
    ip_match = re.search(r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]', received_string)
    if ip_match:
        details["from_ip"] = ip_match.group(1)

    from_by_match = re.search(r'from\s+([\w\.\-]+(?:\s+\([\w\.\-]+\))?)\s*(?:\((?:[^)]*?\[[^\]]+\]|[^)]+)\))?\s+by\s+([\w\.\-]+)', received_string, re.IGNORECASE)
    if from_by_match:
        details["from_host"] = from_by_match.group(1).split(' ')[0]
        details["by_host"] = from_by_match.group(2)

    timestamp_match = re.search(r';\s*(.*)$', received_string)
    if timestamp_match:
        details["timestamp"] = timestamp_match.group(1).strip()
        
    protocol_match = re.search(r'with\s+([^\s;]+)', received_string, re.IGNORECASE)
    if protocol_match:
        details["protocol"] = protocol_match.group(1)

    return details

def extract_email_address_parts(email_string_with_name):
    """Extrait le nom, l'adresse e-mail et le domaine d'une chaîne."""
    if not email_string_with_name:
        return {"name": None, "address": None, "domain": None}
    
    name, address = parseaddr(email_string_with_name)
    domain = address.split('@')[-1] if address and '@' in address else None
    return {"name": name or None, "address": address or None, "domain": domain}

def parse_message_id(message_id_string):
    """Extrait l'ID et le domaine optionnel d'un Message-ID."""
    if not message_id_string:
        return {"id": None, "domain": None}
    
    cleaned_id = message_id_string.strip('<>')
    domain = None
    if '@' in cleaned_id:
        parts = cleaned_id.split('@')
        if len(parts) > 1 and '.' in parts[-1]:
            domain = parts[-1]
    return {"id": cleaned_id, "domain": domain}

def parse_email_headers(all_headers_list):
    """Prend la liste 'all_headers' et retourne un dictionnaire parsé."""
    parsed_info = {
        "authentication_results_summary": [],
        "received_path": [],
        "return_path": None,
        "from_address": None,
        "reply_to_address": None,
        "to_addresses": [],
        "cc_addresses": [], # --- CORRECTION: Ajout de Cc ---
        "message_id": None,
        "subject": None,
        "date": None,
        "x_originating_ip": None,
        "x_mailer": None, # --- CORRECTION: Ajout de X-Mailer ---
        "other_x_headers": {}
    }

    for header in all_headers_list:
        name = header.get("name", "").lower()
        value = header.get("value", "")

        if name in ["authentication-results", "arc-authentication-results"]:
            parsed_info["authentication_results_summary"].append({
                "type": name,
                "server": value.split(';')[0].strip(),
                "parsed_values": parse_authentication_results(value)
            })
        elif name == "received":
            parsed_info["received_path"].append(parse_received_header(value))
        elif name == "return-path":
            parsed_info["return_path"] = extract_email_address_parts(value.strip('<>'))
        elif name == "from":
            parsed_info["from_address"] = extract_email_address_parts(value)
        elif name == "reply-to":
            parsed_info["reply_to_address"] = extract_email_address_parts(value)
        elif name == "to":
            parsed_info["to_addresses"].extend([extract_email_address_parts(addr) for addr in value.split(',') if addr.strip()])
        # --- CORRECTION: Ajout du parsing de Cc ---
        elif name == "cc":
            parsed_info["cc_addresses"].extend([extract_email_address_parts(addr) for addr in value.split(',') if addr.strip()])
        elif name == "message-id":
            parsed_info["message_id"] = parse_message_id(value)
        elif name == "subject":
            parsed_info["subject"] = value
        elif name == "date":
            parsed_info["date"] = value
        elif name == "x-originating-ip":
            parsed_info["x_originating_ip"] = value.strip('[]')
        # --- CORRECTION: Ajout du parsing de X-Mailer ---
        elif name == "x-mailer" or name == "user-agent":
            parsed_info["x_mailer"] = value
        elif name.startswith("x-"):
            parsed_info["other_x_headers"][name] = value
            
    return parsed_info