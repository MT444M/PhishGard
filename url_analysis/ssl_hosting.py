# ssl_hosting.py
# SSL/TLS & Hosting Metadata retrieval for StealthPhisher2025 pipeline
import socket
import ssl
import requests
from datetime import datetime, timezone
from dateutil.parser import parse as dateutil_parse
from config import settings
API_TOKEN = settings.IPINFO_API_KEY

def _parse_ssl_date(date_str: str) -> datetime:
    """
    Parses SSL date strings using the robust dateutil library.
    Example format: 'Jun  1 00:00:00 2025 GMT'
    """
    if not date_str:
        raise ValueError("Date string is empty")
    try:
        # The dateutil parser is very flexible and can handle various formats
        return dateutil_parse(date_str)
    except (ValueError, TypeError) as e:
        # If parsing fails, raise a specific error to avoid continuing with a bad date
        raise ValueError(f"Could not parse date: {date_str}") from e

def format_domain_age(age_days: int) -> str:
    """
    Converts domain age in days to a human-readable format: years, months, days.
    """
    years = age_days // 365
    remaining_days = age_days % 365
    months = remaining_days // 30
    days = remaining_days % 30
    return f"{years} years, {months} months, {days} days"

def get_ssl_info(domain: str, port: int = 443, timeout: int = 5) -> dict:
    """
    Establishes an SSL connection to retrieve certificate details:
      - protocol: the SSL/TLS protocol version used.
      - CertIssuer: the certificate issuer.
      - ValidFrom, ValidTo: the validity period of the certificate.
      - DaysUntilExpiry: raw number of days until expiry.
      - ValidityPeriod: the days_until_expiry converted to a human-readable format (years, months, days).
      
    If an error occurs during the connection or retrieval, the function returns a dictionary with an error message.
    """
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                # CORRECTION: Récupérer le protocole réel de la connexion SSL
                protocol_version = ssock.version()
                cipher_info = ssock.cipher()
                
    except Exception as e:
        return {"error": str(e)}
    
    # Parse the certificate validity dates and make them timezone-aware.
    not_before = _parse_ssl_date(cert['notBefore']).replace(tzinfo=timezone.utc)
    not_after = _parse_ssl_date(cert['notAfter']).replace(tzinfo=timezone.utc)
    days_valid = (not_after - datetime.now(timezone.utc)).days
    validity_period = format_domain_age(days_valid)
    
    # Extraire l'issuer principal du certificat
    issuer_name = "Unknown"
    if cert.get('issuer'):
        for item in cert['issuer']:
            if item[0][0] == 'organizationName':
                issuer_name = item[0][1]
                break
            elif item[0][0] == 'commonName':
                issuer_name = item[0][1]
    
    return {
        "HasSSL": 1,
        "Protocol": protocol_version,  # Protocole réel utilisé (TLSv1.2, TLSv1.3, etc.)
        "CertIssuer": issuer_name,
        "ValidFrom": not_before,
        "ValidTo": not_after,
        "DaysUntilExpiry": days_valid,
        "ValidityPeriod": validity_period,
        "CipherSuite": cipher_info[0] if cipher_info else None,  # Info supplémentaire
        "CipherVersion": cipher_info[1] if cipher_info else None,  # Version du chiffrement
        "CipherBits": cipher_info[2] if cipher_info else None     # Bits de chiffrement
    }

def get_extended_ssl_info(domain: str, port: int = 443, timeout: int = 5) -> dict:
    """
    Version étendue avec plus d'informations sur la sécurité SSL/TLS
    """
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                # Informations détaillées sur la connexion SSL
                protocol_version = ssock.version()
                cipher_info = ssock.cipher()
                
                # Vérifier les extensions du certificat
                cert_extensions = []
                if 'subjectAltName' in cert:
                    cert_extensions.append(('SAN', cert['subjectAltName']))
                
    except Exception as e:
        return {"error": str(e)}
    
    # Parse dates
    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
    days_valid = (not_after - datetime.now(timezone.utc)).days
    validity_period = format_domain_age(days_valid)
    
    # Extraire informations issuer
    issuer_info = {}
    if cert.get('issuer'):
        for item in cert['issuer']:
            key, value = item[0]
            issuer_info[key] = value
    
    # Subject info
    subject_info = {}
    if cert.get('subject'):
        for item in cert['subject']:
            key, value = item[0]
            subject_info[key] = value
    
    return {
        "HasSSL": 1,
        "Protocol": protocol_version,
        "ProtocolSupported": get_supported_protocols(domain, port),
        "CertIssuer": issuer_info.get('organizationName', issuer_info.get('commonName', 'Unknown')),
        "IssuerDetails": issuer_info,
        "SubjectDetails": subject_info,
        "ValidFrom": not_before,
        "ValidTo": not_after,
        "DaysUntilExpiry": days_valid,
        "ValidityPeriod": validity_period,
        "CipherSuite": cipher_info[0] if cipher_info else None,
        "CipherVersion": cipher_info[1] if cipher_info else None,
        "CipherBits": cipher_info[2] if cipher_info else None,
        "Extensions": cert_extensions,
        "SerialNumber": cert.get('serialNumber'),
        "Version": cert.get('version', 1)
    }

def get_supported_protocols(domain: str, port: int = 443, timeout: int = 3) -> list:
    """
    Teste quels protocoles SSL/TLS sont supportés par le serveur
    """
    protocols_to_test = [
        ssl.PROTOCOL_TLS,  # Laisse SSL négocier
        ssl.PROTOCOL_TLSv1_2,
        ssl.PROTOCOL_TLSv1_1,
        ssl.PROTOCOL_TLSv1
    ]
    
    # Ajouter TLSv1.3 si disponible (Python 3.7+)
    if hasattr(ssl, 'PROTOCOL_TLSv1_3'):
        protocols_to_test.insert(1, ssl.PROTOCOL_TLSv1_3)
    
    supported = []
    
    for protocol in protocols_to_test:
        try:
            ctx = ssl.SSLContext(protocol)
            with socket.create_connection((domain, port), timeout=timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    version = ssock.version()
                    if version and version not in supported:
                        supported.append(version)
        except Exception:
            continue
    
    return supported

def test_ssl_info(domain: str):
    """
    Fonction de test pour vérifier la récupération des informations SSL
    """
    print(f"Testing SSL info for: {domain}")
    print("=" * 50)
    
    # Test basique
    basic_info = get_ssl_info(domain)
    print("Basic SSL Info:")
    for key, value in basic_info.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50 + "\n")
    
    # Test étendu
    extended_info = get_extended_ssl_info(domain)
    print("Extended SSL Info:")
    for key, value in extended_info.items():
        if key in ['ValidFrom', 'ValidTo']:
            print(f"  {key}: {value.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            print(f"  {key}: {value}")
def get_ip_geolocation_info(domain: str, api_token: str=API_TOKEN) -> dict: 
    """
    Resolves a domain to its unique IP address(es) and fetches geolocation info for one IP.
    
    Process:
      - Uses socket.getaddrinfo to resolve the domain.
      - Returns a list of unique IPs and their count.
      - If at least one IP is found, fetches geolocation information for the first IP using ipinfo.io.
      
    Parameters:
      - domain: The domain to resolve.
      - api_token: Optional API token for the ipinfo.io service if required.
      
    Returns a dictionary containing:
      - "IPAddresses": List of resolved IP addresses.
      - "IPCount": The number of unique IP addresses.
      - "Geolocation": Geolocation information for the first IP address (if available).
    """
    # Resolve domain to IP addresses
    try:
        infos = socket.getaddrinfo(domain, None)
        ips = list({info[4][0] for info in infos})
    except Exception as e:
        return {"error": f"Error resolving domain: {str(e)}"}
    
    ip_count = len(ips)
    result = {
        "IPAddresses": ips,
        "IPCount": ip_count,
    }
    
    if ip_count > 0:
        # Fetch geolocation information for the first IP
        ip = ips[0]
        url = f"https://ipinfo.io/{ip}/json"
        headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
        except Exception as e:
            result["Geolocation"] = {"error": f"Failed to retrieve geolocation data: {str(e)}"}
        else:
            result["Geolocation"] = {
                "IP": ip,
                "Country": data.get('country'),
                "Region": data.get('region'),
                "City": data.get('city'),
                "Org": data.get('org'),
                "ASN": data.get('org').split(' ')[0] if data.get('org') else None
            }
    
    return result



# def get_shodan_info(ip: str, api_key: str) -> dict:
#     """
#     Queries Shodan API to retrieve open ports, services, and banner info.
#     Requires a valid `api_key`.
#     """
#     url = f"https://api.shodan.io/shodan/host/{ip}?key={api_key}"
#     try:
#         resp = requests.get(url, timeout=5)
#         data = resp.json()
#     except Exception as e:
#         return {"error": str(e)}

#     ports = data.get('ports', [])
#     services = [s.get('product') or s.get('data') for s in data.get('data', [])]

#     return {
#         "OpenPorts": ports,
#         "Services": services,
#         "LastUpdate": data.get('last_update')
#     }


if __name__ == "__main__":
    # Test avec des domaines populaires
    test_domains = ["google.com", "github.com", "stackoverflow.com"]
    for domain in test_domains:
        test_ssl_info(domain)
        print("\n" + "=" * 70 + "\n")
