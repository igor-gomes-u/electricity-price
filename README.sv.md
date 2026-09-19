[![Version](https://img.shields.io/github/v/tag/igor-gomes-u/electricity-price?label=version&sort=semver&color=%238b5cf6)](https://github.com/igor-gomes-u/electricity-price/tags)
[![CI – main](https://github.com/igor-gomes-u/electricity-price/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/igor-gomes-u/electricity-price/actions/workflows/ci.yaml)
[![Coverage](https://github.com/igor-gomes-u/electricity-price/raw/main/.github/badges/coverage.svg)](https://github.com/igor-gomes-u/electricity-price/actions/workflows/ci.yaml)
[![Secret Scan](https://github.com/igor-gomes-u/electricity-price/actions/workflows/secret-scan.yaml/badge.svg?branch=main)](https://github.com/igor-gomes-u/electricity-price/actions/workflows/secret-scan.yaml)
[![CD – DEV](https://github.com/igor-gomes-u/electricity-price/actions/workflows/docker-publish.yaml/badge.svg?branch=main)](https://github.com/igor-gomes-u/electricity-price/actions/workflows/docker-publish.yaml)
[![Promote STAGING](https://github.com/igor-gomes-u/electricity-price/actions/workflows/promote-staging.yaml/badge.svg?branch=main&event=workflow_dispatch)](https://github.com/igor-gomes-u/electricity-price/actions/workflows/promote-staging.yaml)
[![Multi-arch](https://img.shields.io/badge/multi--arch-amd64%20%7C%20arm64-blue)](#)
[![GHCR image](https://img.shields.io/badge/GHCR-image-blue)](https://github.com/users/igor-gomes-u/packages/container/package/electricity-price)
![Trivy](https://img.shields.io/badge/Trivy-image%20scan-red)

🇬🇧 English version:
👉 [Read in English](README.md)

---

> Av Igor Gomes

# Electricity Price Sweden — Application Repository

Ett DevOps-fokuserat projekt som demonstrerar ett komplett leveransflöde, inklusive CI/CD, GitOps, kontinuerliga säkerhetskontroller, observability, policy enforcement och kontrollerad miljö-promotion, baserat på en egenutvecklad applikation.

## Översikt

### Det här repositoryt ansvarar för
- applikationskod
- tester, lint och coverage
- säkerhetsskanning
- build och publicering av container image (artifact)
- triggar deployment till ett GitOps-repository

### Separat GitOps-repository ansvarar för
- deployment och miljö-promotion (DEV → STAGING → PROD)
- runtime-konfiguration och Helm-baserad deployment
- validering, säkerhet och policy enforcement (GitHub Actions + OPA)
- observability, dashboards och alerting i Kubernetes
- rollback genom deklarativ GitOps-styrning

> Tillsammans visar de ett komplett flöde från applikationskod till deployment via GitOps i ett Kubernetes-kluster.

## Relaterade Repository

**GitOps (deployment & environment promotion):** [electricity-price-gitops](https://github.com/igor-gomes-u/electricity-price-gitops)

## End-to-end CI/CD och GitOps-arkitektur

<p align="center">
  <img src="docs/images/architecture.png" alt="Applikation och GitOps-arkitektur">
  <br>
  <em>Övergripande CI/CD-flöde från applikationsbuild till GitOps-styrd deployment.</em>
</p>

> **Obs (säkerhet):** Pipelines i repositoryt kör kontinuerliga säkerhetsskanningar (**Trivy**, **Gitleaks**). Upptäckta secrets blockeras automatiskt av **Gitleaks** och stoppar flödet. Sårbarheter i beroenden och container image kan tillfälligt förekomma, identifieras av **Trivy** och hanteras löpande genom planerade uppdateringar.
>
> **Underhåll:** Dependabot används för schemalagda och kontrollerade uppdateringar av Python-beroenden, GitHub Actions och Docker base image.
>
> **Container build:** Imagen byggs via en multi-stage Dockerfile med en non-root runtime-image, låst digest för basimagen och health checks. Verktyg som endast används under byggprocessen ingår inte i den slutliga runtime-imagen, vilket minskar attackytan.
>
> **Runtime Protection:** Inkluderar inbyggd begränsning av förfrågningsstorlek, rate limiting för beräkningar och globala HTTP security headers för säker publik deployment.

## Projektöversikt

### Vad
> Python-baserad Flask-webbapplikation som visar elpriser för olika delar av Sverige per datum  
> (tabell + diagram), baserat på extern realtids-API.

### Varför
> Byggd för att fungera som grund för ett tillförlitligt och produktionsnära leveransflöde.

### Värde
> Stateless design utan databas ger ett förutsägbart driftbeteende och underlättar horisontell
> skalning i Kubernetes. 

> Projektet visar ett komplett leveransflöde med tester, coverage och säkerhetsskanning,
> där ett immutabelt container artifact levereras och används i ett separat GitOps-repository
> för kontrollerad miljö-promotion.

### Avgränsningar
> Beroende av extern API och dess publiceringstider samt begränsat datumintervall.  
> Ingen caching (avsiktligt utanför scope).

## Datakälla

**Elprisdata (publikt API):** [Elpriset just nu – elpris-api](https://www.elprisetjustnu.se/elpris-api)

## Teknikstack

| Komponent         | Syfte / Roll                         |
|-------------------|--------------------------------------|
| Python            | Applikationsspråk                    |
| Flask             | Webbramverk (API & UI)               |
| Jinja2            | Template-rendering                   |
| HTML / Bootstrap  | UI (frontend)                        |
| Pandas            | Databehandling                       |
| Plotly            | Interaktiva diagram                  |
| pytest            | Enhetstestning                       |
| prometheus-client | Metrik och monitoring                |

## Dependency management

Projektet separerar runtime- och testberoenden i separata filer.

| Fil                     | Innehåll                               | Användning                 |
|-------------------------|----------------------------------------|----------------------------|
| `requirements.txt`      | Runtime-beroenden för applikationen    | Bygga container image      |
| `requirements-test.txt` | Test-, coverage- och CI-verktyg        | CI-pipeline och lokal test |
   
---

## Applikationsbeskrivning

Den Flask-baserade webbapplikationen låter användaren söka efter elpriser för olika delar av Sverige för ett valt datum. Applikationen visar timvisa elpriser (00:00–23:00). Data hämtas från en extern API, bearbetas med Pandas och presenteras i tabellform samt som interaktiva Plotly-diagram.

## Funktioner

- Formulär för att välja datum
- Hämtar elprisdata automatiskt via API
- Visar resultat i tabellformat
- Interaktiv diagram-visualisering
- Hälsokontroller: `/healthz` och `/readyz`
- Prometheus-metrik på `/metrics`
- Fullt enhetstestad med `pytest`

---

## Installation & Körning (lokalt)

### 1️⃣ Klona projektet

```bash
git clone https://github.com/igor-gomes-u/electricity-price.git
cd electricity-price
```

### 2️⃣ Starta applikationen (Docker)

```bash
docker compose up -d
```

> Detta använder en publicerad och verifierad release-image av applikationen, hämtad direkt från GHCR.

### 3️⃣ Öppna i webbläsaren

- Applikationen: `http://localhost:38080`

<p align="center">
  <img src="docs/images/app-home.png" alt="Applikationens startvy med formulär">
  <br>
  <em>Formulär för att välja datum och område för att beräkna elpriser.</em>
</p>

### 4️⃣ Databearbetning och visualisering

- Resultatvy visas efter att formuläret har skickats in

<p align="center">
  <img src="docs/images/result-overview.png" alt="Resultatvy med diagram och sammanfattning">
  <br>
  <em>Bearbetad elprisdata visualiserad med Plotly samt sammanfattning av resultat.</em>
</p>

<p align="center">
  <img src="docs/images/result-table.png" alt="Timvisa elpriser i tabellform">
  <br>
  <em>Timvisa elpriser presenterade i tabellformat (Pandas).</em>
</p>

---

## Viktiga endpoints

| Endpoint     | Funktion                             |
|--------------|--------------------------------------|
| `/`          | Startvy med formulär                 |
| `/calculate` | Beräknar och visar elprisdata        |
| `/healthz`   | Liveness-check                       |
| `/readyz`    | Readiness-check                      |
| `/metrics`   | Prometheus-metrik                    |

> **Obs:** Endpointen `/calculate` används via formuläret i webbgränssnittet och är inte avsedd att anropas direkt i webbläsaren (HTTP POST).
>
> **Prometheus-metrik:** `/metrics` är aktiverad som standard. Sätt `METRICS_ENABLED=false` för att inaktivera publik åtkomst och returnera HTTP 404.

## CI/CD-pipelines (Build → PR till GitOps → Deployment)

Build, säkerhetskontroller och publicering av container image till GitHub Container Registry (GHCR) hanteras av pipelines i application repository, medan deployment och miljö-promotion utförs via ett separat GitOps repository.

Promotioner initieras från application repository via `repository_dispatch`. Varje miljö har ett dedikerat workflow, och promotion sker stegvis:

- DEV bygger, publicerar och validerar artefakten innan STAGING triggas.
- STAGING promouterar och validerar artefakten samt förbereder en release candidate.  
- PROD promouterar den validerade release candidate via en SemVer-baserad release.  

Dessa workflows triggar events i GitOps repository, där Pull Requests skapas. När dessa mergas synkroniserar Argo CD desired state och deployar till respektive miljö (DEV, STAGING, PROD).

### Workflows i Application Repository

> Promotion mellan miljöer återanvänder samma immutable image digest som byggs en gång i DEV.

#### **Secret Scan (`secret-scan.yaml`)** 
– secret scanning med Gitleaks  

#### **CI (`ci.yaml`)** 
– linting, formatting checks, tester och coverage  

#### **CD – DEV (`docker-publish.yaml`)**
  - Bygger och publicerar en immutable multi-arch image till GHCR
  - Kör ett smoke test av den publicerade containerimagen via dess digest och validerar hälsostatus, Prometheus-metrik och applikationens startvy
  - Genererar SBOM och kör Trivy security scans
  - Skickar `update-dev` event till GitOps
  - ➝ I GitOps repository: en Pull Request skapas och auto-mergas i DEV
  - Triggar nästa steg i promotion-flödet (STAGING workflow)

#### **Promote STAGING (`promote-staging.yaml`)**
  - Resolverar eller tar emot image digest från DEV  
  - Skickar `promote-staging` event till GitOps  
  - ➝ I GitOps repository: en Pull Request skapas för manuell review i STAGING  
  - Markerar det validerade image digestet som aktuell **release candidate** i container-registret  

#### **Release PROD (`release-prod.yaml`)**
  - Triggas manuellt via SemVer-tagg (`vX.Y.Z`)  
  - Promoterar aktuell **release candidate** till PROD  
  - Skapar en versions-tag (`vX.Y.Z`) i GHCR (utan rebuild)  
  - Skickar `release-prod` event till GitOps  
  - ➝ I GitOps repository: en Pull Request skapas för manuell review innan deployment  

#### **Dependabot Updates (`dependabot.yaml`)**
- Uppdaterar GitHub Actions-dependenser  
- Uppdaterar Python-paket  
- Uppdaterar Docker base image-referenser  
- Körs enligt ett månatligt schema  
- Öppnar ett begränsat antal Pull Requests för granskning

---

## Projektstruktur

```text
electricity-price/
├── .github/workflows/      # CI/CD-workflows (CI, Docker publish, secret-scan, promote-staging, release-prod)
├── application/            # Flask-applikation: routes, logik, templates och statiska filer
├── docs/                   # Dokumentation (t.ex. skärmdumpar, extra beskrivningar)
├── tests/                  # Pytest-tester för applikationen
├── .dockerignore           # Utesluter onödiga filer från Docker build-context
├── .gitignore              # Ignorerade filer (virtuell miljö, cache, rapporter, etc.)
├── .gitleaks.toml          # Regler för secret scanning (Gitleaks)
├── .ruff.toml              # Konfiguration för Ruff (lint och format)
├── docker-compose.yaml     # Lokal körning med Docker Compose
├── Dockerfile              # Multi-stage build för produktionsimagen
├── pytest.ini              # Pytest-konfiguration (plugins, options)
├── requirements.txt        # Runtime-beroenden för applikationen
├── requirements-test.txt   # Test- och CI-beroenden
├── README.md               # Projektöversikt, användning och arkitektur (engelska)
└── README.sv.md            # Projektöversikt, användning och arkitektur (svenska)
```

---

## Kontakt

Igor Gomes — DevOps Engineer  
**E-post:** [igor.gomes.u@gmail.com](mailto:igor.gomes.u@gmail.com)  
**LinkedIn:** [Igor Gomes](https://www.linkedin.com/in/igor-gomes-5b6184290)