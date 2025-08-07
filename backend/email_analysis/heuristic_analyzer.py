# PhishGard-AI/analysis/heuristic_analyzer.py

# La signature de la fonction est modifiée pour accepter les résultats OSINT
def analyze_header_heuristics(parsed_headers, osint_results):
    """
    Analyse les en-têtes avec une logique de scoring v3 qui intègre
    les données d'enrichissement OSINT.
    """
    score = 0
    flags = {
        "positive": [],
        "negative": []
    }

    # --- Accès sécurisé aux données parsées (inchangé) ---
    from_addr = parsed_headers.get("from_address") or {}
    from_domain = from_addr.get("domain")
    return_path_addr = parsed_headers.get("return_path") or {}
    return_path_domain = return_path_addr.get("domain")
    reply_to_addr = parsed_headers.get("reply_to_address") or {}
    reply_to_domain = reply_to_addr.get("domain")
    
    auth_summary = parsed_headers.get("authentication_results_summary", [])
    primary_auth = next((res.get("parsed_values", {}) for res in auth_summary if res.get("type") == "authentication-results"),
                        (auth_summary[0].get("parsed_values", {}) if auth_summary else {}))

    # --- 1. Analyse de l'Authentification (inchangé) ---
    auth_strength = "weak"
    # DMARC
    dmarc_results = primary_auth.get("dmarc", [])
    if not dmarc_results:
        score -= 10
        flags["negative"].append("DMARC_RECORD_MISSING (-10)")
    else:
        dmarc = dmarc_results[0]
        if dmarc.get("result") == "pass":
            policy = dmarc.get("policy")
            if policy in ["reject", "quarantine"]:
                score += 25
                flags["positive"].append("DMARC_PASS_STRICT (+25)")
                auth_strength = "strong"
            else:
                score += 10
                flags["positive"].append("DMARC_PASS_MONITOR (+10)")
                auth_strength = "moderate"
        elif dmarc.get("result") == "fail":
            score -= 30
            flags["negative"].append("DMARC_FAIL (-30)")
    # DKIM
    dkim_results = primary_auth.get("dkim", [])
    if not dkim_results:
        score -= 10
        flags["negative"].append("DKIM_SIGNATURE_MISSING (-10)")
    else:
        for dkim in dkim_results:
            if dkim.get("result") == "fail":
                score -= 20
                flags["negative"].append(f"DKIM_FAIL(domain:{dkim.get('domain')}) (-20)")
            elif dkim.get("result") == "pass":
                if from_domain and dkim.get("domain") and dkim.get("domain").endswith(from_domain):
                    score += 15
                    flags["positive"].append(f"DKIM_PASS_ALIGNED(domain:{dkim.get('domain')}) (+15)")
                    if auth_strength != "strong": auth_strength = "moderate"
                else:
                    score -= 5
                    flags["negative"].append(f"DKIM_PASS_UNALIGNED(domain:{dkim.get('domain')}) (-5)")
    # SPF
    spf_results = primary_auth.get("spf", [])
    if not spf_results:
        score -= 10
        flags["negative"].append("SPF_RECORD_MISSING (-10)")
    else:
        spf = spf_results[0]
        if spf.get("result") == "pass":
            score += 5
            flags["positive"].append("SPF_PASS (+5)")
        elif spf.get("result") in ["fail", "softfail"]:
            score -= 10
            flags["negative"].append(f"SPF_{spf.get('result').upper()} (-10)")

    # --- 2. Analyse des Incohérences de Domaine (inchangé) ---
    if from_domain and return_path_domain and not return_path_domain.endswith(from_domain):
        if auth_strength == "weak":
            score -= 5
            flags["negative"].append("FROM_RETURN_PATH_MISMATCH_WEAK_AUTH (-5)")
    if reply_to_domain and from_domain and not reply_to_domain.endswith(from_domain):
        score -= 15
        flags["negative"].append(f"REPLY_TO_DOMAIN_MISMATCH(from:{from_domain}, reply-to:{reply_to_domain}) (-15)")

    # --- 3. NOUVEAU: Scoring basé sur l'Enrichissement OSINT ---
    
    # Âge du domaine de l'expéditeur
    if from_domain and from_domain in osint_results["domain_analysis"]:
        domain_info = osint_results["domain_analysis"][from_domain]
        if "age_days" in domain_info:
            age = domain_info["age_days"]
            if age < 30:
                score -= 25
                flags["negative"].append(f"OSINT_DOMAIN_VERY_RECENT(age:{age}d) (-25)")
            elif age < 180:
                score -= 15
                flags["negative"].append(f"OSINT_DOMAIN_RECENT(age:{age}d) (-15)")
            elif age > 730:
                score += 10
                flags["positive"].append(f"OSINT_DOMAIN_ESTABLISHED(age:{age}d) (+10)")
            elif age > 365:
                score += 5
                flags["positive"].append(f"OSINT_DOMAIN_MATURE(age:{age}d) (+5)")
    
    # Réputation et nature de l'IP d'envoi
    # (On prend la première IP trouvée dans le chemin, qui est la plus proche de la source)
    if osint_results["ip_analysis"]:
        source_ip_analysis = osint_results["ip_analysis"][0]
        
        # Score AbuseIPDB
        if "abuseipdb" in source_ip_analysis and "abuseConfidenceScore" in source_ip_analysis["abuseipdb"]:
            abuse_score = source_ip_analysis["abuseipdb"]["abuseConfidenceScore"]
            if abuse_score > 80:
                score -= 30
                flags["negative"].append(f"OSINT_IP_BLACKLISTED(abuse_score:{abuse_score}) (-30)")
            elif abuse_score > 25:
                score -= 15
                flags["negative"].append(f"OSINT_IP_SUSPICIOUS(abuse_score:{abuse_score}) (-15)")

        # Fournisseur de l'IP
        if "ipinfo" in source_ip_analysis and "org" in source_ip_analysis["ipinfo"]:
            org = source_ip_analysis["ipinfo"]["org"].lower()
            known_good_providers = ["google", "microsoft", "amazon", "mailgun", "salesforce"]
            if any(provider in org for provider in known_good_providers):
                score += 5
                flags["positive"].append("OSINT_IP_FROM_KNOWN_PROVIDER (+5)")

    # --- 4. Détermination de la Classe Finale (seuils inchangés) ---
    assessment = ""
    if score >= 20:
        assessment = "LEGITIME"
    elif score <= -20:
        assessment = "PHISHING"
    else:
        assessment = "SUSPICIOUS"

    # --- 5. Construction de l'objet de retour final ---
    final_results = {
        "classification": assessment,
        "score": score,
        "details": {
            "authentication_strength": auth_strength,
            "positive_indicators": flags["positive"],
            "negative_indicators": flags["negative"]
        }
    }
    return final_results