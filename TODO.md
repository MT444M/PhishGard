# TODO PhishGard

Liste des tâches à faire :

1. Améliorer la présentation de l'analyse détaillée. DONE
2. Ajouter dans l'analyse détaillée le nombre de liens analysés avec leurs détails d'analyse. DONE
3. revoir la récupération du time et l'affichage. DONE
4. développer le module analyse des liens. DONE
5. détailler les json final_report  
    * "llm_analysis": {
      "classification": "SUSPICIOUS",
      "reason": "L'email contient des liens suspects, des offres trop belles...",
      "keywords": ["liens suspects", "offres trop belles"]
    }

    *    "url_ml_analysis": {
      "prediction": "legitimate",
      ...,
      "details": [
        { "url": "http://exemple-securise.com", "verdict": "legitimate", "score": 0.95 },
        { "url": "http://lien-suspect.net", "verdict": "suspicious", "score": 0.85 }
      ]
    }. DONE
6. (?). DONE
                        //////////////////////////////////////////////////////////////////

7. ajouter onglets "Web Technologies" et "Reputation"



// python -m http.server 8080
// sudo -u postgres psql

# remove WebsitePhishingDetection from Github


--- Analyse complète terminée. ---
{

  "phishgard_verdict": "Legitime",

  "confidence_score": "50.0%",

  "final_score_internal": 50.0,

  "summary": "Agrégation des analyses heuristique, URL et LLM.",

  "breakdown": {

    "heuristic_analysis": {

      "classification": "LEGITIME",

      "score": 55,

      "details": {

        "authentication_strength": "strong",

        "positive_indicators": [

          "DMARC_PASS_STRICT (+25)",

          "DKIM_PASS_ALIGNED(domain:tldrnewsletter.com) (+15)",

          "SPF_PASS (+5)",

          "OSINT_DOMAIN_ESTABLISHED(age:2575d) (+10)",

          "OSINT_IP_FROM_KNOWN_PROVIDER (+5)"

        ],

        "negative_indicators": [

          "DKIM_PASS_UNALIGNED(domain:amazonses.com) (-5)"

        ]

      }

    },

    "url_ml_analysis": {

      "prediction": "legitimate",

      "probability_phishing": "25.00%",

      "probability_legitimate": "75.00%"

    },

    "llm_analysis": {

      "classification": "LEGITIME",

      "confidence_score": "10",

      "reason": "L'email est un communiqué public et informatif, avec des liens et des offres claires, sans menaces ou doute."

    },

    "osint_enrichment": {

      "ip_analysis": [

        {

          "ip": "54.240.77.24",

          "ipinfo": {

            "ip": "54.240.77.24",

            "hostname": "a77-24.smtp-out.amazonses.com",

            "city": "Seattle",

            "region": "Washington",

            "country": "US",

            "loc": "47.5846,-122.3005",

            "org": "AS14618 Amazon.com, Inc.",

            "postal": "98144",

            "timezone": "America/Los_Angeles"

          },

          "abuseipdb": {

            "ipAddress": "54.240.77.24",

            "isPublic": true,

            "ipVersion": 4,

            "isWhitelisted": null,

            "abuseConfidenceScore": 0,

            "countryCode": "US",

            "usageType": "Data Center/Web Hosting/Transit",

            "isp": "Amazon Web Services, Inc.",

            "domain": "amazon.com",

            "hostnames": [

              "a77-24.smtp-out.amazonses.com"

            ],

            "isTor": false,

            "totalReports": 0,

            "numDistinctUsers": 0,

            "lastReportedAt": null

          }

        }

      ],

      "domain_analysis": {

        "amazonses.com": {

          "creation_date": "2010-06-04T23:55:10",

          "age_days": 5541

        },

        "dailyupdate.tldrnewsletter.com": {

          "creation_date": "2018-07-19T02:35:03",

          "age_days": 2575

        },

        "tldrnewsletter.com": {

          "creation_date": "2018-07-19T02:35:03",

          "age_days": 2575

        }

      },

      "path_analysis": {

        "hop_countries": [

          "US"

        ],

        "hop_delays_seconds": [

          1

        ]

      }

    }

  }

} 