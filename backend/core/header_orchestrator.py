# PhishGard-AI/core/header_orchestrator.py

import json
from email_analysis import header_parser, heuristic_analyzer, osint_enricher
from core.final_aggregator import FinalAggregator

def parse_raw_header_to_list(raw_header: str):
    """
    Convertit une chaîne de caractères d'en-tête brut en une liste de
    dictionnaires que header_parser peut utiliser.
    """
    header_list = []
    # Les en-têtes peuvent être sur plusieurs lignes (continuation lines)
    # On les regroupe d'abord.
    full_header_lines = raw_header.strip().split('\n')
    current_header = None
    for line in full_header_lines:
        if line.startswith((' ', '\t')) and current_header:
            # C'est une ligne de continuation
            current_header['value'] += ' ' + line.strip()
        elif ':' in line:
            # C'est une nouvelle ligne d'en-tête
            if current_header:
                header_list.append(current_header)
            name, value = line.split(':', 1)
            current_header = {'name': name.strip(), 'value': value.strip()}
    if current_header:
        header_list.append(current_header)
    return header_list


class HeaderOrchestrator:
    """
    Orchestre l'analyse d'un en-tête d'e-mail brut fourni à la demande.
    """
    def run_header_analysis(self, raw_header: str):
        """
        Exécute le pipeline d'analyse complet pour un en-tête.
        """
        print("\n--- Début de l'orchestration pour l'analyse de header à la demande ---")

        # 1. Conversion et Parsing du header
        print("[1/4] Parsing des en-têtes...")
        header_list = parse_raw_header_to_list(raw_header)
        parsed_headers = header_parser.parse_email_headers(header_list)

        # 2. Enrichissement OSINT
        print("[2/4] Lancement de l'enrichissement OSINT...")
        osint_results = osint_enricher.enrich_with_osint_data(parsed_headers)

        # 3. Analyse Heuristique
        print("[3/4] Lancement de l'analyse heuristique...")
        heuristic_results = heuristic_analyzer.analyze_header_heuristics(parsed_headers, osint_results)

        # 4. Agrégation finale (avec des résultats vides pour les modules non applicables)
        print("[4/4] Agrégation des résultats...")
        
        # On crée des résultats "vides" ou "neutres" pour les analyses non effectuées
        # car nous n'avons pas le corps de l'e-mail.
        url_model_results = {"prediction": "N/A", "details": "Analyse d'URL non applicable (header seulement)."}
        llm_results = {"classification": "N/A", "confidence_score": 0, "details": "Analyse LLM non applicable (header seulement)."}

        aggregator = FinalAggregator(
            heuristic_results=heuristic_results,
            url_model_results=url_model_results,
            llm_results=llm_results,
            osint_results=osint_results,
            email_id="on-demand-header-analysis" # ID générique
        )
        final_report = aggregator.calculate_final_verdict()
        print("\n--- Résultats de l'analyse de header à la demande : ---")
        print(final_report)
        print("--- Analyse de header terminée. ---")

        return final_report
    

## Exemple d'utilisation
if __name__ == "__main__":
    raw_header = """Delivered-To: mthiam716@gmail.com
Received: by 2002:a05:6520:3214:10b0:2cf:21f4:8dff with SMTP id 20-n1csp1340545lkw;
        Thu, 21 Aug 2025 22:38:59 -0700 (PDT)
X-Google-Smtp-Source: AGHT+IHFmTL7J41T6xiAICExfeEzGoLQ94iIrkcdRaAE/NNXl4Ey29foZDfQue3iOTgEeSaUutEb
X-Received: by 2002:a05:6a00:3981:b0:73c:b86:b47f with SMTP id d2e1a72fcca58-7702f9d90cfmr2389120b3a.4.1755841138770;
        Thu, 21 Aug 2025 22:38:58 -0700 (PDT)
ARC-Seal: i=1; a=rsa-sha256; t=1755841138; cv=none;
        d=google.com; s=arc-20240605;
        b=h1O6E3U3c3ybZT++kbybEaCS593XuZ8+isg3z/KmzBVN+7VfPYtgpbL1ZUHfYHgZvd
         e0tbIFwebG4zGeeC3bPCJHrxHDw6gNAhes6InkT8ihcVXY7ekdXi3+b3Ut+FGkiCovu6
         npP89/80NKUdbJDd6pzaPNafMvDRs3KkiOvk6xFJnl4tS5lHJIjxRU7FlCxd1WemGxZd
         O+fcDaTdMOJNi9zQp7Q9yjv2PRzZ1WZzSfjrGiPZmRYE+cQak5whvaKxxYFEj7IlI1TH
         QEWXupye9Tf5tO9gWY9JU6rcmcfVR6Byerqfwd4a2GJuS6fZJKE5as5bDK+pRNrEe5DI
         vidg==
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20240605;
        h=feedback-id:message-id:reply-to:mime-version:list-unsubscribe-post
         :list-unsubscribe:date:subject:to:from:dkim-signature:dkim-signature;
        bh=kJRBWB+POvRlZeeep7MwitgTuc9Fde3JeHbWxchBEa8=;
        fh=PoXJ5V6cr4xsQVDtXAkqQL5mO5jMYzCQQwEqlMh2+ME=;
        b=jvgbT+KH0JybOXQX18ZKpFjz15J8gsAMfSwqLTtMFShulFcCywSU+0cU2wzQLmdGBD
         rljy+VORSYfEI5dBtqgX74N55tw9jcp0QIFEUHxo0FvO7/9MgvvuDApeFVwr/mTUix4j
         GCQbWhs+n3N9WcSuR938tUWRROfSRCojhK7I4+3FBOHoCfQ3+ZobXsbyQgAMcxv2Otuj
         6UEbGYAQ6H2XMS2+GFwCGZHCr+/s092GqIOCiflLTSlTIyxBE+xVBElM4qpmPNK6qWBo
         dAVMXevq6nnYvMblP9cHhBcH7Kmm2jfcEmLWW0TNpHZbriSQvIwaflTcVPPMZHp0xYmQ
         lrzw==;
        dara=google.com
ARC-Authentication-Results: i=1; mx.google.com;
       dkim=pass header.i=@alertes.seloger.com header.s=51dkim1 header.b=VwBrDPRn;
       dkim=pass header.i=@s51.y.mc.salesforce.com header.s=fbldkim51 header.b=ZU3NvAFn;
       spf=pass (google.com: domain of bounce-6_html-8064667-17538-536006699-585226@bounce.by.seloger.com designates 159.92.154.25 as permitted sender) smtp.mailfrom=bounce-6_HTML-8064667-17538-536006699-585226@bounce.by.seloger.com;
       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=alertes.seloger.com
Return-Path: <bounce-6_HTML-8064667-17538-536006699-585226@bounce.by.seloger.com>
Received: from mta4.by.seloger.com (mta4.by.seloger.com. [159.92.154.25])
        by mx.google.com with ESMTPS id d2e1a72fcca58-76e7d254e22si5843968b3a.430.2025.08.21.22.38.57
        for <mthiam716@gmail.com>
        (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128);
        Thu, 21 Aug 2025 22:38:58 -0700 (PDT)
Received-SPF: pass (google.com: domain of bounce-6_html-8064667-17538-536006699-585226@bounce.by.seloger.com designates 159.92.154.25 as permitted sender) client-ip=159.92.154.25;
Authentication-Results: mx.google.com;
       dkim=pass header.i=@alertes.seloger.com header.s=51dkim1 header.b=VwBrDPRn;
       dkim=pass header.i=@s51.y.mc.salesforce.com header.s=fbldkim51 header.b=ZU3NvAFn;
       spf=pass (google.com: domain of bounce-6_html-8064667-17538-536006699-585226@bounce.by.seloger.com designates 159.92.154.25 as permitted sender) smtp.mailfrom=bounce-6_HTML-8064667-17538-536006699-585226@bounce.by.seloger.com;
       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=alertes.seloger.com
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; s=51dkim1; d=alertes.seloger.com; h=From:To:Subject:Date:List-Unsubscribe:List-Unsubscribe-Post:MIME-Version: Reply-To:Message-ID:Content-Type; i=annonces@alertes.seloger.com; bh=kJRBWB+POvRlZeeep7MwitgTuc9Fde3JeHbWxchBEa8=; b=VwBrDPRnL7z2BBfSH8h4UcB/e/REqgQvTcCZUK79aSUByZ+W7UBgIn4m2YlzgbjDVEnHRS73OgBt
   B5HZ9mv3Erfyfmeewr3AAA28EtDn/MSNZgjbmKH+oTw3cevFxIGHQibDQxvDnHB4H/2A36N0E+Do
   yIAxmO+cEyu7C0dvQKNPZwMD1U8kDNJqOTQwx/erjdx21xpQI2wpPo2f4E5ASsL4Oxb/km9j6qcJ
   BiTPeK4GzlPWfo8xkEXnKZKBiH2A4IntZLdKHthpCOcXBrnt3qKAWJN3E4qicHd3V5BMLbB+jqVI
   UWFiqUXXfZ7iF6m11R/7nWA7QgYkJdAcl5803Q==
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; s=fbldkim51; d=s51.y.mc.salesforce.com; h=From:To:Subject:Date:List-Unsubscribe:MIME-Version:Reply-To:Message-ID: Content-Type; bh=kJRBWB+POvRlZeeep7MwitgTuc9Fde3JeHbWxchBEa8=; b=ZU3NvAFndF3XkdJZIpAHmVInAG5AGGOKJeWkXOJ/TtqhX1posBaSKMTKWyRNGfd8T0LEc/xTpWOS
   5yLLW9XJjsmZ0grQE7RnBLHY2rPXxjvVL38uSR88sjFcrOo0iMGjXg+oJGHbzUViXjRmP9T3IHLR
   mlnMv4K9MimGio7gqCUG/izH8G45qGPY10aOojTEPwOLkeEiGQCSxlX8MK/KPgc3ZAHwub865oBz
   UWXazqAzwyPwjfVYIiy/IDOPnrDRMVEZ2T+wUXLFZqhWfpzfw8bAHxqCW89COGS5OnYeoitqeLI1
   zq7v7ykvhbr63YMKvjtFDDavBp9A5PkO/IJ8tg==
Received: by mta4.by.seloger.com id hl01742fmd4k for <mthiam716@gmail.com>; Fri, 22 Aug 2025 05:37:45 +0000 (envelope-from <bounce-6_HTML-8064667-17538-536006699-585226@bounce.by.seloger.com>)
From: SeLoger <annonces@alertes.seloger.com>
To: <mthiam716@gmail.com>
Subject: 1 nouvelle annonce : Évry
Date: Thu, 21 Aug 2025 23:37:45 -0600
List-Unsubscribe: <https://click.by.seloger.com/subscription_center.aspx?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtaWQiOiI1MzYwMDY2OTkiLCJzIjoiODA2NDY2NyIsImxpZCI6IjYiLCJqIjoiMTc1MzgiLCJqYiI6IjU4NTIyNiIsImQiOiI1MTAwMDQifQ.8BALjMgUtOi1MnbTcafc5PIKTuvmV0xdKr1xArfp7O4>, <mailto:leave-fdb5121f2d205921-fe8a1c707360027b72-fef7157770670c-fe2311737364047b731d79-fec311787066067b@leave.by.seloger.com>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
MIME-Version: 1.0
Reply-To: SeLoger <reply-fef7157770670c-6_HTML-8064667-536006699-585226@by.seloger.com>
x-messageKey: 81b02279-eb83-4383-ac50-8fbcfb26507c
X-Delivery: Transactional
X-SFMC-Stack: 51
x-job: 536006699_17538
Message-ID: <4db61866-7388-465d-9376-216d00006d2c@cdg3s51mta92.xt.local>
Feedback-ID: 536006699:17538:159.92.154.25:sfmktgcld
Content-Type: multipart/alternative; boundary="gk8Ch4R0wRM3=_?:"

--gk8Ch4R0wRM3=_?:
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 8bit






1 nouvelle annonce : Évry📬 Trop de mails ? Vous pouvez facilement passer à 
https://click.by.seloger.com/?qs=d0e181daa703d8e287b1b2168fb5e152a62e71558c35b9edb50f28926e2339187621dc0f397e66d0359c820b6714499d20e1ed149e2535c55db67a60815bfa29 
un mail par jour ou mettre en pause les envois  pour le moment.

https://click.by.seloger.com/?qs=d0e181daa703d8e287b1b2168fb5e152a62e71558c35b9edb50f28926e2339187621dc0f397e66d0359c820b6714499d20e1ed149e2535c55db67a60815bfa29 
Modifier mes alertes &rarr; 

https://click.by.seloger.com/?qs=d0e181daa703d8e23b4f75eaef7f6fc3150547a13dbb0f88cc8d4bc9b70fac62abc184db5699f53c2770d57aef1637ea5915f9aac9d37e1982c150565434e2d0 

1 nouvelle annonce pour vous à Évry

 
  


 

 


 
  

 https://click.by.seloger.com/?qs=d0e181daa703d8e2ac14d708757aade5619c516317e3cf52eadabbaf181a1047abe943a7b740b57b3eaa5e365b55a5106ed9c343f1184d088900711c3b3a7767 


 
 
 
https://click.by.seloger.com/?qs=d0e181daa703d8e26018d94c3ac2214f6602752173e62e9ff6743b34ae4d524405afa9727270355d1aadef8628819282331024a15afcdaf5ad376414f98484d5 
500 €/mois cc

https://click.by.seloger.com/?qs=d0e181daa703d8e28140e3f8c8855b43609cc9bc475b1a26ec7468e6c453833a4a59c01b766a5fd6106fbb747684253d4af86d8b103290f4276ecfa67048f0ea 
Belle chambre dans coloc 68m² rénovée

https://click.by.seloger.com/?qs=d0e181daa703d8e24ecf5921eb5f4369ca7fc7ef94504aa7290651c8d5036acba48e804aad9629d5be4e679201e6c7a290aa29f64da01cea83dda3ef6d30b58d 
1 pièce . 68 m² 

https://click.by.seloger.com/?qs=d0e181daa703d8e28450eb6da988836b85feab1da1fb24b5cc5a6258be32203837703ebbd32d4582d6da224404933362a2f5ba697684a7033102549b14420f7f 

 Centre Urbain Nord, 
 
 Évry-Courcouronnes
 (91000)
  

https://click.by.seloger.com/?qs=d0e181daa703d8e2ba490f3bee510aefafd89d4f3227b4363c0ae45ba9aeeb37c0304361bc57236f27aa9ea6899f506f75da7e7ebc5e8ce63bb55c4ec5b81631 
Voir l'annonce 





https://click.by.seloger.com/?qs=d0e181daa703d8e2b04ba6152b2fca09acd7895643d804a12b009e80494647c0c89094f7417cca04110371c60378cc0a4fc034d85b41c79586053c698285aaaa 
Vous souhaitez investir dans l'immobilier locatif ?
  






 

 
 

 
Changez facilement la fréquence d'envoi
Vous pouvez choisir de recevoir des alertes 
en temps réel ou 1 fois/jour.

https://click.by.seloger.com/?qs=d0e181daa703d8e2c84abd6a25ab18ae0b7d09a07273e5a4cb7965855333d016a15c164d0a059eb6964819e76d381b5563acaba098aeb7decf305787ff6ae776 
Changer la fréquence &rarr; 

https://click.by.seloger.com/?qs=d0e181daa703d8e2c84abd6a25ab18ae0b7d09a07273e5a4cb7965855333d016a15c164d0a059eb6964819e76d381b5563acaba098aeb7decf305787ff6ae776 
Gérer mes alertes et abonnements  |
 
https://click.by.seloger.com/?qs=d0e181daa703d8e2b9174cfbac9d812cc75c44f840761f61fd32af78b341bd6dc41c945d0827d96b80cbe60e5ac43dccc59207c53c2b80e92e190f5b7f705caf 
Arrêter cette alerte 

 

Avez-vous l'application SeLoger?
 

https://click.by.seloger.com/?qs=d0e181daa703d8e209f76c575dcab88b51a932124f64cc1f8763377bd5113d9ce578a1d87f01b1f8d01287bd27cb792933d5d5770f4975fcab812b9c3f3bd6c7 
 
https://click.by.seloger.com/?qs=d0e181daa703d8e209f76c575dcab88b51a932124f64cc1f8763377bd5113d9ce578a1d87f01b1f8d01287bd27cb792933d5d5770f4975fcab812b9c3f3bd6c7 

 

https://click.by.seloger.com/?qs=d0e181daa703d8e27168853116cb0b7646da3f4346b7c15ade094578d960c6e52a68c4195b706aff729354ebb811246adbd32ff7b4a6aad2db12ce43f5a1036d 
Politique de Confidentialité  . 
 
https://click.by.seloger.com/?qs=d0e181daa703d8e2f994892c0ae03c8c7762cc98b3ea4075840385ab4c9b08f2895272016bd4e8e951b149ded29a2f8eeca668b0a87d7814163145f00f386ea9 
Conditions Générales d'Utilisation 
Cet e-mail vous a été envoyé sur mthiam716@gmail.com parce que vous avez souscrit à une alerte sur SeLoger.
 

 SeLoger / Digital Classifieds France . 2-8, rue des Italiens . 75009 Paris

 Conformément à la loi Informatique et Libertés, vous pouvez accéder aux données vous concernant, les faire rectifier ou demander leur effacement. Vous disposez également d'un droit d'opposition, d'un droit à la portabilité et d'un droit à la limitation du traitement des données qui vous concernent.
 

SeLoger • 
https://view.by.seloger.com/?qs=3432dafaf20e9734f177a0dbd7463cbcfb591f1eea7f2a0175f2a7a6df102e8b603140f25b0051ec32ca93975bdce8f56f0ae2535343f17982fe59e3fc2092b2aa7379ab68db156bd3d989ba2f5c9b5a 
SLG-202505-ALI-STANDARD 



--gk8Ch4R0wRM3=_?:
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 8bit






<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="fr">
<head>
    <meta name="HandheldFriendly" content="True">
    <meta name="format-detection" content="telephone=no date=no, address=no, email=no">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="x-apple-disable-message-reformatting">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>1 nouvelle annonce : Évry</title>
    <link rel="preconnect" href="https://website-assets.seloger.com">
    
    <!--[if (mso 16)]>     <style type="text/css">     a {text-decoration: none;}     </style>     <![endif]--><!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]--><!--[if gte mso 9]>     <xml>     <o:OfficeDocumentSettings>     <o:AllowPNG></o:AllowPNG>     <o:PixelsPerInch>96</o:PixelsPerInch>     </o:OfficeDocumentSettings>     </xml>     <![endif]-->
 <style type="text/css">
    html{
        margin: 0;
    }
    body{
        margin: 0;
        background-color: #F9F9F9;
        font-family: 'CeraSL', Helvetica, Arial, sans-serif !important;
        font-weight: normal !important;
        font-style: normal !important;
    }
    #outlook a {
        padding:0;
    }
    span.MsoHyperlink,
    span.MsoHyperlinkFollowed {
        color:inherit;
        mso-style-priority:99;
    }
    a.es-button {
        mso-style-priority:100!important;
        text-decoration:none!important;
    }
    a[x-apple-data-detectors] {
        color:inherit!important;
        text-decoration:none!important;
        font-size:inherit!important;
        font-family:inherit!important;
        font-weight:inherit!important;
        line-height:inherit!important;
    }

    /* Re-style iPhone automatic links (eg. phone numbers) */
    .appleLinks a {
        color: #1C3452;
        text-decoration: none;
    }
    .appleLinksGrey a {
        color: #323232;
        text-decoration: none;
    }
    .appleLinksWhite a {
        color: #ffffff !important;
        text-decoration: none !important;
    }

/*FONTS*/
@media screen
 {
 .foo
  {
   /*ORANGE MAIL*/
  }
 @font-face {
 font-family: 'CeraSL';
 font-style: normal;
 font-weight: 400;
 src: url(https://website-assets.seloger.com/commons/fonts/cera-sl/CeraSLsys-Regular.woff2) format('woff2');
    font-display:swap;
  }
 @font-face {
    font-family: 'CeraSL';
 font-style: bold;
 font-weight: 700;
 src: url(https://website-assets.seloger.com/commons/fonts/cera-sl/CeraSLsys-Bold.woff2) format('woff2');
    font-display:swap;
  }
 }
    
    /*RESPONSIVE*/
 @media only screen and (max-width:320px)
  {
   .foo {
      /*ORANGE MAIL*/  }
    .fixiOS {
     width: 320px !important; }
    .mobile-button {
        align: center !important;
        text-align: center !important; }
    .mobile-button span {
        align: center !important;
        text-align: center !important;
        max-width:600px !important;
        width: 100% !important; }
    .mobile-button a {
        align: center !important;
        text-align: center !important;
        display:block !important;
        padding:8px 16px 8px 16px !important; }
    .col-auto {
        width: 100% !important;
        display: block; }
    .pt-16 {
        padding-top: 16px!important; }
    .pt-6 {
        padding-top: 6px!important; }
    .pb-8 {
        padding-bottom: 8px!important;  }
    .pb-16 {
        padding-bottom: 16px!important; }
    .pt-24 {
        padding-top: 16px!important;  }
    .pl-24 {
        padding-left: 24px!important;
        padding-right: 24px!important  }
    .mobile-teaser {
        align: center !important;
        text-align: center !important;  }
  }
 @media only screen and (min-width:321px) and (max-width:420px)
  {
   .foo {
        /*ORANGE MAIL*/  }
    .fixiOS {
        width: 419px !important; }
    .mobile-button {
        align: center!important;
        text-align: center !important; }
    .mobile-button span {
        max-width:600px !important;
        width: 100% !important; }
    .mobile-button a {
        align: center !important;
        text-align: center !important;
        display:block !important;
        padding:8px 16px 8px 16px !important; }
    .col-auto {
        width: 100% !important;
        display: block; }
    .pt-16 {
        padding-top: 16px!important; }
    .pt-6 {
        padding-top: 6px!important; }
    .pb-8 {
        padding-bottom: 8px!important;  }
    .pb-16 {
        padding-bottom: 16px!important; }
    .pt-24 {
        padding-top: 24px!important; }
    .pl-24 {
        padding-left: 24px!important;
        padding-right: 24px!important; }
    .mobile-teaser {
        align: center !important;
        text-align: center !important; }
   }
  @media screen and (max-width:640px)
  {
   .foo {
        /*ORANGE MAIL*/
    }
    .container-fluid {
        width: 100% !important }
    .container-90 {
        width: 91.25% !important;
        min-width: 310px;  }
    .container-75 {
        width: 75% !important  }
    .d-none {
        display: none!important;  }
    .img-fluid {
        width: 100% !important;
        height: auto !important; }
    .col-auto {
        width: 270px;
        display: block;  }
    .mobile-button {
        align: left!important ;
        text-align: left;
        width:auto }
    .mobile-teaser {
        align: left;
        text-align: left  }
    .h-200 {
        height: 200px!important;     }
    .es-mobile-hidden, .es-hidden  {
        display:none!important     }
    .es-desk-hidden  { 
        width:auto!important; overflow:visible!important; float:none!important; max-height:inherit!important; line-height:inherit!important }
   }    

 </style>
</head>
<body class="body" style="width:100%;height:100%;padding:0;Margin:0"><style type="text/css">
div.preheader 
{ display: none !important; } 
</style>
<div class="preheader" style="font-size: 1px; display: none !important;">1 nouvelle annonce correspondant à vos critères ont été publiés. Jetez-y un coup d’œil!</div>  
 <div style="background-color:#F9F9F9" lang="fr">
 <!--[if gte mso 9]>   <v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">    <v:fill type="tile" color="#F9F9F9"></v:fill>   </v:background>  <![endif]-->

<!--MAIN CONTAINER-->
  <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;padding:0;Margin:0;width:100%;height:100%;background-repeat:repeat;background-position:center top;background-color:#F9F9F9"  cellpadding="0" cellspacing="0" width="100%">
   <tr>
    <td style="padding:0;Margin:0" valign="center">  
     <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:640px" bgcolor="#FFFFFF" border="0" cellpadding="0" cellspacing="0" width="640" align="center">
      <tr>
       <td>
   <!--UNSUB HEADER-->  
        <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;" width="640" bgcolor="#FDF2E4" cellspacing="0" cellpadding="0" border="0" align="center">
         <tr>
          <td>
           <table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" bgcolor="#FDF2E4" cellspacing="0" cellpadding="0" border="0" align="center">
            <tr>
             <th align="left" class="mobile-teaser col-auto " style="Margin:0px;padding:20px 0px 20px 0px;width:380px">
              <table class="container-fluid mobile-teaser pb-8" role="presentation" border="0" cellpadding="0" cellspacing="0" bgcolor="#FDF2E4" align="left">
               <tr>
                <td>
                 <span style="Margin:0; mso-line-height-rule:exactly; letter-spacing:0; font-size:12px;font-weight:bold;line-height:18px;color:#2B2B2B;">📬 Trop de mails ? Vous pouvez facilement passer à  <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e250589f7bd9cb70a68b5bca9c5a8e60037d2ef41486d6b7bf32262cdacb32f6dc7c7bf114129779c2249c1f6755ee11bc2326700a1cee8923"  name="box_sachange"  target="_blank" style="color: #2B2B2B; text-decoration: underline;">un mail par jour ou mettre en pause les envois</a> pour le moment.</span>
                </td>
               </tr>
              </table>
             </th>
             <th width="5" class="d-none">
             <th class="mobile-teaser col-auto " align="right" style="Margin:0;padding:20px 0px 20px 0px;width:175px" >
              <table class="container-fluid mobile-teaser pt-6 pb-16" role="presentation" border="0" cellpadding="0" cellspacing="0" bgcolor="#FDF2E4" align="right">
               <tr>
                <td >
                 <span style="border-style:solid;border-color:#2B2B2B;background:#2B2B2B;border-width:2px;display:inline-block;border-radius:25px;width:auto"><a href="https://click.by.seloger.com/?qs=d0e181daa703d8e250589f7bd9cb70a68b5bca9c5a8e60037d2ef41486d6b7bf32262cdacb32f6dc7c7bf114129779c2249c1f6755ee11bc2326700a1cee8923" name="link_sachange"  style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#2B2B2B;font-size:12px;padding:4px 16px 4px 16px;display:inline-block;background:#FDF2E4;border-radius:25px;font-weight:bold;line-height:18px;width:auto;text-align:left;letter-spacing:0;mso-padding-alt:4px;mso-border-alt:2px solid #2B2B2B" target="_blank">Modifier mes alertes&nbsp;&rarr;</a></span>
                </td>
               </tr>
              </table>
             </th>
            </tr>
           </table>
          </td>
         </tr>
        </table>
   <!--END UNSUB HEADER-->        
   <!--LOGO-->  
        <table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" bgcolor="#FFFFFF" cellspacing="0" cellpadding="0" border="0" align="center">
         <tr>
          <td align="center" style="Margin:0px;padding:40px 0px 40px 0px;width:100%;">
           <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e293631950645dce0d9eb0a29bce6f844d63bf66cfbad3f04d6b86f79a5deb5ebd556ae60ebf666d2330dcfb1bb61dc673f7071d9fc9dffb2d" target="_blank" style="text-decoration:none;" name="logo" ><img src="https://image.by.seloger.com/lib/fe2311737364047b731d79/m/1/eadcb611-0848-4dad-a9aa-3e8a3513263c.png" alias="logo" name="logo" alt="seloger_logo" width="149" border="0" style="display: block;"></a>
          </td>
         </tr>
        </table>
   <!--END LOGO-->
        
    <!--HERO TITLE-->
        <table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" cellspacing="0" cellpadding="0" border="0" align="center">
         <tbody>
          <tr>
           <td style="Margin:0;padding:0px 0px 16px 0px; background-color:#FFFFFF;" bgcolor="#FFFFFF" align="center">
            <h1 style="Margin:0;mso-line-height-rule:exactly; letter-spacing:0; font-size:24px;font-weight:bold;line-height:32px;color:#000000;">1 nouvelle annonce pour vous à Évry</h1>
           </td>
          </tr>
         </tbody>
        </table>
   <!--END HERO TITLE-->
         
    


 

         


         
   <!--LISTING-->

    <table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" cellspacing="0" cellpadding="0" border="0" align="center">
     <tr>
      <td style="Margin:0;padding:24px 0px 24px 0px; background-color:#FFFFFF;" bgcolor="#FFFFFF" align="center">
       <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" cellspacing="0" cellpadding="0" border="0" align="center">
        <tr> 

<!-- Start Object Picture--> 

          <th align="left" class="col-auto" valign="top">
          <table class="container-fluid" role="presentation" border="0" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" align="center" width="270">
           <tr>
            <td Background="https://mms.seloger.com/9/6/4/b/964bd7f7-6d20-4449-a3c6-bdeb78b4deed.jpg?ci_seal=41b720a9d9123111bde85001ccce525d723481a2&h=370&w=500" style="background-image: url('https://mms.seloger.com/9/6/4/b/964bd7f7-6d20-4449-a3c6-bdeb78b4deed.jpg?ci_seal=41b720a9d9123111bde85001ccce525d723481a2&h=370&w=500'); background-repeat: no-repeat; background-size: cover; background-position:center; height: 200px; -webkit-border-radius: 16px; -moz-border-radius: 16px; border-radius:16px;" class="h-200" valign="top">
                <!--[if gte mso 12]>                 <v:image xmlns:v="urn:schemas-microsoft-com:vml" style="width:270px;height:200px;" color="#ffffff" src="https://mms.seloger.com/9/6/4/b/964bd7f7-6d20-4449-a3c6-bdeb78b4deed.jpg?ci_seal=41b720a9d9123111bde85001ccce525d723481a2&h=370&w=500" />                 <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="false" stroke="false" style="position:relative;width:270px;height:200px;">                 <v:textbox inset="0,0,0,0">                 <![endif]-->
              <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2872ab8f7bf9f5d11355308def72f8d40df727484b01106104d6057a83f419ec6c21d4805a7cbf93ac1b425df5cf951f1e0f5d76062a60b0d" name="adimage1_1"  style="border: none; text-decoration: none;" target="_blank">
               <table  role="presentation" align="center" border="0" cellspacing="0" cellpadding="0"class="container-fluid" >
                <tr>
                 <td width="270" height="200" class="h-200" align="left">
                  <img src="https://image.by.seloger.com/lib/fe2311737364047b731d79/m/1/b01678d0-d0be-4b7b-b270-99bc76c25ef3.png" alt="" width="270" height="200" style="display: block;" class="img-fluid">
                 </td>
                </tr>
               </table>
              </a>
             <!--[if gte mso 12]>     </v:textbox>     </v:rect>     <![endif]-->
            </td>
           </tr>
          </table>
         </th>
                      
          
        <!-- End Object Picture-->

         <th width="20" class="d-none">
         </th>
         <th align="right" class="col-auto pt-16" width="270">
          <table class="container-fluid" role="presentation" border="0" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" align="left">
           <tr>
            <td align="left" style="Padding:0px 0px 0px 0px; color: #2B2B2B; line-height:32px;">
             <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2ff055ad83ffc82e18e2cc61f4b665c398f16dd8dbbf7ba020ff51a07af09f733ef0efd6fc2e3c7fa104f7fc294031a7c87e9bfb657e844b5" name="adprice1_1"  style="color: #2B2B2B; font-size:24px; line-height:32px; text-decoration: none; font-style: normal" target="_blank"><span style="color: #2B2B2B; font-size:24px; line-height:32px; text-decoration: none; font-weight: normal;font-style: normal" ><strong>500 €/mois </strong></span><span style="color: #262626; font-size:14px; line-height:20px; text-decoration: none;font-weight: normal;font-style: normal" >cc</span></a>
            </td>
           </tr>
           <tr>
            <td align="left" style=" Padding:4px 0px 0px 0px; color: #262626; font-size:16px;line-height:24px;">
             <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2f1f0e7678b82868d885e7dc4d72a8998ebc230f0c32900ca5b055e35308541092fdcb3ff597c54c519a66393effa4879452c4e95b72a2ee7" name="adtype1_1"  target="_blank" style="color: #262626; text-decoration: none;font-style: normal;font-weight: normal;"><strong>Belle chambre dans coloc 68m² rénovée</strong></a>
            </td>
           </tr>
           <tr>
            <td align="left" style="Padding:4px 0px 0px 0px; color: #262626; font-size:14px; line-height:20px;">
             <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e201b1e2a08ad6fab6ee29236cc5b73c95c0157a5fa5b0e9c42a0e669f22bd1eff2ceb62132de301620059517e20c8629931f8166453f8f58b" name="adcriteria1_1"  target="_blank" style="color: #262626; text-decoration: none; font-weight: normal">1 pièce &middot; 68 m²</a>
            </td>
           </tr>
           <tr>
            <td align="left" style="Padding:4px 0px 0px 0px; color: #262626; font-size:14px; line-height:20px;font-style: normal">
             <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2656360eecdc41d32a4410d5f5588fdc6350d3cca25f043938bee716e25d606c0e41c3dab48793ca5c9a970fd48dbc7ff81fb3b34c82134f3" name="adlocation1_1"  target="_blank" style="color: #646464; text-decoration: none; font-style: normal; font-weight: normal">
             Centre Urbain Nord, 
             
             Évry-Courcouronnes
             (91000)
             </a>
            </td>
           </tr>
           <tr>
            <td class="mobile-button" style="Margin:0;padding:16px 0px 0px 0px;" ><span style="border-style:solid;border-color:#2B2B2B;background:#2B2B2B;border-width:2px;display:inline-block;border-radius:25px;width:auto"><a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2bc4a1b3e4fc17223d094443f07462dbff54665f349bc9aefd3490777cc7644ad6aac380abf2a524f16571a74c3ee80a42b8b7b0b025ba2a4" name="adbutton1_1"  style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#2B2B2B;font-size:16px;padding:4px 16px 4px 16px;display:inline-block;background:#FFFFFF;border-radius:25px;font-style: normal; font-weight:bold;line-height:24px;width:auto;text-align:left;letter-spacing:0;mso-padding-alt:4px;mso-border-alt:2px solid #2B2B2B" target="_blank">Voir l'annonce</a></span>
            </td>
           </tr>
          </table>
         </th>
        </tr>
       </table>
      </td>
     </tr>
    </table>
<!--END LISTING-->



<!--Ads BLOCK-->
<table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px; background-color:#FFFFFF;" width="560" cellspacing="0" cellpadding="0" border="0" align="center"> 
  <tr>
   <td style="Padding: 8px 0 24px 0;">
    <table role="presentation" align="center" border="0" width="100%" cellspacing="0" cellpadding="0" style="width: 100%;" class="container-fluid">
     <tr>
      <td style="Padding: 16px 32px; border: 1px solid #E0E0E0; border-radius: 16px; font-size: 16px; line-height: 24px; display: block;" align="center">
       <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2b04ba6152b2fca09acd7895643d804a12b009e80494647c0c89094f7417cca04110371c60378cc0a4fc034d85b41c79586053c698285aaaa" style="color: #000000; text-decoration: none; ">Vous souhaitez investir dans l'immobilier locatif ?
       <img src="https://image.by.seloger.com/lib/fe2311737364047b731d79/m/1/faadaeb5-9204-4b45-9dc4-f17002af2316.png" height="12" style="Padding: 0 0 0 8px">
       </a>
      </td>
     </tr>
    </table>
   </td>
  </tr>
 </table>
<!--END Ads BLOCK-->




<!--LISTING SPACER-->
<table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px; background-color:#FFFFFF;" width="560" cellspacing="0" cellpadding="0" border="0" align="center">
  <tr>
   <td height="1" bgcolor="#E0E0E0" style="height:1px; line-height:1px; mso-line-height-alt:1px; mso-line-height:1px; mso-line-height-rule: exactly; mso-height-alt:1px; mso-height:1px; mso-height-rule: exactly; font-size:1px;">&nbsp;</td>
  </tr>
 </table>
<!--END LISTING SPACER-->
         
            

 <!--UNSUB BLOCK-->      
 <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:640px" bgcolor="#FFFFFF" border="0" cellpadding="0" cellspacing="0" width="640" align="center">
  <tr>
   <td style="Margin:0;padding:24px 0px 24px 0px">
    <table class="container-90"  role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px; border-radius:16px;background-color:#F9F9F9; width:560px" width="560" bgcolor="#F9F9F9" cellspacing="0" cellpadding="0" border="0" align="center">
     <tr>
      <td style="Margin:0;padding:24px 0px 24px 0px; border-radius:16px;" align="center">
       <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px; border-radius:16px;background-color:#F9F9F9;width:560px" width="560" cellspacing="0" cellpadding="0" border="0" align="center" bgcolor="#F9F9F9">
        <tr>  
          <th align="left" class="col-auto pb-8 mobile-teaser" valign="middle" >
            <table class="container-fluid pl-24 mobile-teaser" role="presentation" border="0" cellpadding="0" cellspacing="0" bgcolor="#F9F9F9" align="center">
             <tr> 
              <td style="Margin:0;padding:0px 24px 0px 24px" align="center" valign="middle">
                <img src="https://image.by.seloger.com/lib/fe2311737364047b731d79/m/1/a385eb83-989c-4c47-bdd7-1df107a892e0.png" height="62" style="display: block;" >
              </td>
             </tr>
            </table>
          </th> 
          <th align="right" class="col-auto mobile-teaser" valign="middle" >
           <table class="container-fluid pl-24 mobile-teaser" style="Padding:0px 24px 0px 0px;" role="presentation" border="0" cellpadding="0" cellspacing="0" bgcolor="#F9F9F9"  width="100%">
            <tr>
             <td class="mobile-teaser" style="color: #000000; font-size:16px; line-height:24px;font-style: normal;font-weight: normal">
              <b>Changez facilement la fréquence d'envoi</b><br>
              <span style="display: block; font-size: 14px; line-height: 18px;font-style: normal;font-weight: normal">Vous pouvez choisir de recevoir des alertes <br class="d-none">en temps réel ou 1 fois/jour.</span>
             </td>
            </tr>
            <tr>
             <td  class="mobile-teaser" style=" color: #E30613; font-size:14px; line-height:24px;">
              <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2550ac1e9aec0b4e6bddd83db3ea6ba4c528fb5fc43182761678de1d0ad3bd3c6e6ad39fe71ddd0799cc266f6493dadb0345f1e6860f63f15"  name="box_sachange"  target="_blank" style="color: #E30613; text-decoration: none;font-style: normal;font-weight: normal">Changer la fréquence&nbsp;&rarr;</a>
             </td>
            </tr>
           </table>
          </th>
        </tr>
       </table>  
      </td>
     </tr>
    </table>
    <table class="container-90"  role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px; border-radius:16px;background-color:#F9F9F9; width:560px" width="560" bgcolor="#F9F9F9" cellspacing="0" cellpadding="0" border="0" align="center">
     <tr>
      <td style="Margin:0;padding:24px 0px 0px 0px; background-color:#FFFFFF; mso-line-height-rule:exactly; letter-spacing:0; font-size:16px;line-height:24px;color:#323232;text-decoration:none;" bgcolor="#FFFFFF" align="center">
          <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2f72d76580d2e2da1252958c35e90c37c6d0e155a3647953630dff44c4a05d62871de30399e336e870f69039a346b0ac87c2f5d94eb032f55" target="_blank" style="color: #323232; text-decoration:underline;"  name="footer_sachange">Gérer mes alertes et abonnements</a> |
          <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e262361951c9ebb1c1cb6180ee85b82fe575ea3e3269edda7b7a29edeadfc5511884acc3a20a299fa41f6bcbfb415772f07cb8136a7e8e9230" target="_blank" style="color: #323232; text-decoration:underline;" name="footer_saunsubscribe" >Arrêter cette alerte</a>
      </td>
     </tr>
    </table>
   </td>
  </tr>
 </table>
<!--END UNSUB BLOCK--> 
<!--SPACER-->
<table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px; background-color:#FFFFFF;" bgcolor="#FFFFFF" width="560" cellspacing="0" cellpadding="0" border="0" align="center">
  <tr>
   <td height="1" bgcolor="#E0E0E0" style="height:1px; line-height:1px; mso-line-height-alt:1px; mso-line-height:1px; mso-line-height-rule: exactly; mso-height-alt:1px; mso-height:1px; mso-height-rule: exactly; font-size:1px;">&nbsp;</td>
  </tr>
 </table>
<!--END SPACER-->

       </td>
      </tr>
     </table>
                 
  <!--FOOTER-->  
     <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:640px" bgcolor="#FFFFFF" border="0" cellpadding="0" cellspacing="0" width="640" align="center">
      <tr>
       <td>
        <table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" bgcolor="#FFFFFF" cellspacing="0" cellpadding="0" border="0" align="center">
           <tr>
            <td style="Margin:0;padding:24px 0px 12px 0px; background-color:#FFFFFF; mso-line-height-rule:exactly; letter-spacing:0; font-size:16px;line-height:24px;color:#323232;text-decoration:none;" bgcolor="#FFFFFF" align="center">Avez-vous l'application SeLoger?
            </td>
           </tr>
           <tr>
            <td valign="middle" align="center" style="Margin:0;padding:0px 0px 24px 0px;">
             <table align="center" border="0" cellpadding="0" cellspacing="0">
              <tr>
               <td align="right" style="padding:0;Margin:0px;">
                <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e2c69ef647b8d9db3ee47ad685b241b2831d1ca893be91ae46b1d1a0bf7e6c9ffc6f86325dbb785204450748a06ddd6378b9c2ee639b2c3086" target="_blank" style="text-decoration:none;" name="footer_logo_apple" ><img src="https://image.by.seloger.com/lib/fe2311737364047b731d79/m/1/a40bd5c6-cab9-4e6b-b53b-e7a5c0c1d7dc.png" name="footer_app_apple" alt="app_logo_apple" height="40" border="0" style="display: block; text-decoration:none;"></a>
               </td>
               <td width="12">&nbsp;</td>
               <td align="left" style="padding:0;Margin:0px;">
                <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e222e67a6d16189065769ade023f027fc4d746b721c770db392949bee7589c1cc90a05e907824cab15b819b43960b122061b8193c9f68b090a" target="_blank" style="text-decoration:none;" name="footer_logo_android" ><img src="https://image.by.seloger.com/lib/fe2311737364047b731d79/m/1/5d72e23e-df1d-4e6f-aade-b7e601b1aac6.png" name="footer_app_android"  alt="app_logo_android" height="40" border="0" style="display: block; text-decoration:none;"></a>
               </td>
              </tr>
             </table>
            </td>           
           </tr>
     <!--SPACER LINE--> 
           <tr>
            <td height="1" bgcolor="#E0E0E0" style="height:1px; line-height:1px; mso-line-height-alt:1px; mso-line-height:1px; mso-line-height-rule: exactly; mso-height-alt:1px; mso-height:1px; mso-height-rule: exactly; font-size:1px;">&nbsp;</td>
           </tr>
     <!--END SPACER LINE-->
           <tr>
            <td style="Margin:0;padding:24px 0px 24px 0px; background-color:#FFFFFF; mso-line-height-rule:exactly; letter-spacing:0; font-size:12px;line-height:16px;color:#323232;text-decoration:none;" bgcolor="#FFFFFF" align="center">
                <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e231115cb609f28fb470c11d386d267b147bfa3bf50ef252375a32774bb8cc239c5ccdc68dffcd9d2bd0a94320ad5df0c24d55d1befab96626" target="_blank" style="color: #323232; text-decoration:underline;" name="footer_privacy" >Politique de Confidentialité</a> &middot; 
                <a href="https://click.by.seloger.com/?qs=d0e181daa703d8e29b1523cbd0b3a48ed50eb9868f2cc8378906a9ea12c8f14912c6e7b32475cddcfbae227610ace0542ed414d79eda1619ec558277de063cad" target="_blank" style="color: #323232; text-decoration:underline;" name="footer_help" >Conditions Générales d'Utilisation</a>
            </td>
           </tr>
           <tr>
            <td style="Margin:0;padding:0px 0px 16px 0px; background-color:#FFFFFF;mso-line-height-rule:exactly; letter-spacing:0; font-size:12px;line-height:16px;color:#323232;text-decoration:none;" bgcolor="#FFFFFF" align="center">Cet e-mail vous a été envoyé sur <span class="appleLinksGrey">mthiam716@gmail.com</span> parce que vous avez souscrit à une alerte sur SeLoger.
            </td>
           </tr>
           <tr>
            <td style="Margin:0;padding:0px 0px 16px 0px; background-color:#FFFFFF; mso-line-height-rule:exactly; letter-spacing:0; font-size:12px;line-height:16px;color:#323232;text-decoration:none;" bgcolor="#FFFFFF" align="center">
            SeLoger / Digital Classifieds France &middot; <span class="appleLinksGrey">2-8, rue des Italiens &middot; 75009 Paris</span>
            </td>
           </tr>
           <tr>
            <td style="Margin:0;padding:0px 0px 24px 0px; background-color:#FFFFFF; mso-line-height-rule:exactly; letter-spacing:0; font-size:12px;line-height:16px;color:#323232;text-decoration:none;" bgcolor="#FFFFFF" align="center">
            Conformément à la loi Informatique et Libertés, vous pouvez accéder aux données vous concernant, les faire rectifier ou demander leur effacement. Vous disposez également d'un droit d'opposition, d'un droit à la portabilité et d'un droit à la limitation du traitement des données qui vous concernent.
            </td>
           </tr>
          </table>  
         </td>
        </tr>
     </table>
  <!--END FOOTER--> 
  <!--START TEMPLATE NAME-->
    <table class="container-fluid" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#F9F9F9;width:640px" bgcolor="#F9F9F9" border="0" cellpadding="0" cellspacing="0" width="640" align="center">
      <tr>
       <td>
        <table class="container-90" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:560px" width="560" bgcolor="#F9F9F9" cellspacing="0" cellpadding="0" border="0" align="center">
          <tr>
           <td style="Padding:0px 0px 8px 0px; text-align: center; font-size: 6px; line-height: 16px; color: #AAAAAA;">SeLoger • <a href="https://view.by.seloger.com/?qs=3432dafaf20e9734f177a0dbd7463cbcfb591f1eea7f2a0175f2a7a6df102e8b603140f25b0051ec32ca93975bdce8f56f0ae2535343f1792d21553271b1f1889da405a4859af65dd7147e64ea47624c"  title="webversion" style="color: #AAAAAA; text-decoration: none;">SLG-202505-ALI-STANDARD</a>
           </td>
          </tr>
        </table> 
       </td>
      </tr>
    </table>
  <!--END TEMPLATE NAME-->
    </td>
   </tr>
      <!--OPEN TRACKING--> 
<img src="https://click.by.seloger.com/open.aspx?ffcb10-fef7157770670c-fe4e1c78716d07747611-fe2311737364047b731d79-ffc912-fe8a1c707360027b72-fec311787066067b&d=510004&bmt=0" width="1" height="1" alt=""> 
  <!--END OPEN TRACKING--> 
 </table>
<!--END MAIN CONTAINER-->
</div> 
</body>
</html>

--gk8Ch4R0wRM3=_?:--"""
    orchestrator = HeaderOrchestrator()
    result = orchestrator.run_header_analysis(raw_header)
    print(json.dumps(result, indent=2))