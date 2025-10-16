# 🦊 StoreAPI — Modulares Django REST API für E-Commerce

**Verfügbare Sprachen:**  
[🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

---

## 🚀 Übersicht

**StoreAPI** ist ein modularer Backend-Dienst für moderne E-Commerce-Plattformen, entwickelt mit **Django** und **Django Rest Framework**.  
Er bietet die vollständige Funktionalität eines Online-Shops – von der Verwaltung des Produktkatalogs über Bestellungen und Bewertungen bis hin zu SEO-Seiten.

Das Projekt ist derzeit in der Produktion bereitgestellt und wird aktiv genutzt.

> 🔒 Die Module `users` und `auth` wurden **aus Sicherheitsgründen** aus dem Repository entfernt,  
> da das Projekt produktiv im Einsatz ist.

---

## 🧩 Hauptfunktionen

- 📦 Produktkatalog mit Kategorien, Listings, Kollektionen und Marken-Auswahlen  
- 🛒 Warenkorb, Produktvergleich, Favoriten und zuletzt angesehene Produkte  
- 💬 Produktbewertungen und Bewertungssystem  
- 🧾 Erstellung, Verarbeitung und Nachverfolgung von Bestellungen  
- 📰 Blog-Modul mit Artikeln und Metadaten  
- 🧩 SEO-Seiten für Produkte, Kategorien und Artikel  
- 🔎 Volltextsuche mit **MeiliSearch**  
- 📊 Beliebtheits- und Analyseindizes  
- 🤖 Telegram-Integration für Benachrichtigungen und Systemmeldungen  
- ⚙️ Celery + Redis für Hintergrundaufgaben und zeitgesteuerte Jobs  

---

## ⚙️ Technologie-Stack

| Komponente | Zweck |
|-------------|--------|
| **Python 3.12+** | Hauptprogrammiersprache |
| **Django** | Web-Framework |
| **Django REST Framework** | Implementierung der REST-API |
| **PostgreSQL** | Hauptdatenbank |
| **Redis** | Cache und temporäre Datenspeicherung |
| **MeiliSearch** | Volltext-Suchmaschine |
| **Celery + Redis** | Aufgabenwarteschlangen und geplante Jobs |
| **Docker / Docker Compose** | Containerisierung und Bereitstellung |
| **MyPy, Flake8, Black, iSort** | Code-Qualität und Linting-Tools |

---

## 🧱 Modulare Architektur

StoreAPI folgt einer klaren, modularen Struktur:

| Modul | Beschreibung |
|--------|---------------|
| `store` | Produkte, Kategorien, Listings, Marken und Filter |
| `orders` | Bestellverwaltung und Checkout |
| `reviews` | Produktbewertungen und Ratings |
| `banners` | Werbebanner |
| `cart` | Warenkorb |
| `compare` | Produktvergleich |
| `favorites` | Favoriten |
| `images` | Bildverarbeitung und Uploads |
| `ranking_index` | Verwaltung der Beliebtheitsindizes |
| `recently_viewed` | Zuletzt angesehene Produkte |
| `search` | Volltextsuche nach Produkten |
| `short_links` | Mechanismus für Kurzlinks |
| `tags_importers` | Automatische Tag-Zuweisung nach Zeitplan |
| `telegram` | Telegram-Benachrichtigungen |
| `web_pages` | SEO-Seiten für Produkte, Kataloge und Artikel |
| `blog` | Artikel, Kategorien und Inhaltsverwaltung |
| `customer` | Kundendaten und Profile |
| `utils` | Gemeinsame Tools, Cache, Validatoren, Formatierung usw. |

---

## 🧠 Codequalität & Standards

StoreAPI erfüllt moderne Python-Entwicklungsstandards:

```bash
mypy .
flake8 .
black .
isort .
```

- 100 % typisierter Code
- Einheitliches Formatieren und Importsortierung
- Einheitliches Formatieren und Importsortierung

## 🧩 Zusätzliche Funktionen

- SEO-optimierte Metadaten für alle Produkt- und Katalogseiten
- Bereitgestellte REST-Endpunkte zur einfachen Frontend-Integration
- Modulare Struktur für Skalierbarkeit und einfache Erweiterung
- Docker-basierte Umgebung für konsistente Entwicklung und Produktion