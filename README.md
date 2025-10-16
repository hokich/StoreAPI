# 🦊 StoreAPI — Modular Django REST API for E-Commerce

**Available languages:**  
[🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

---

## 🚀 Overview

**StoreAPI** is a modular backend for a modern e-commerce platform, built with **Django** and **Django Rest Framework**.  
It provides full online store functionality — from product catalog management to order processing, reviews, and SEO pages.

The project is currently deployed and used in production.

> 🔒 The `users` and `auth` modules have been **excluded** from the repository for security reasons,  
> since the project is live in production.

---

## 🧩 Key Features

- 📦 Product catalog with categories, listings, collections, and brand selections  
- 🛒 Shopping cart, comparison, favorites, and recently viewed products  
- 💬 Product reviews and rating system  
- 🧾 Order creation, processing, and history tracking  
- 📰 Blog module with structured articles and metadata  
- 🧩 SEO pages for products, categories, and articles  
- 🔎 Full-text search powered by **MeiliSearch**  
- 📊 Popularity ranking and analytics indexes  
- 🤖 Telegram integration for notifications and service messages  
- ⚙️ Celery + Redis for background tasks and cron jobs  

---

## ⚙️ Tech Stack

| Component | Purpose |
|------------|----------|
| **Python 3.12+** | main programming language |
| **Django** | web framework |
| **Django REST Framework** | REST API implementation |
| **PostgreSQL** | main relational database |
| **Redis** | cache and temporary data store |
| **MeiliSearch** | full-text search engine |
| **Celery + Redis** | task queues and scheduled jobs |
| **Docker / Docker Compose** | containerization and deployment |
| **MyPy, Flake8, Black, iSort** | code quality and linting tools |

---

## 🧱 Modular Architecture

StoreAPI follows a clean, modular structure:

| Module | Description |
|--------|--------------|
| `store` | products, categories, listings, brands, and filters |
| `orders` | order management and checkout |
| `reviews` | product reviews and ratings |
| `banners` | promotional banners |
| `cart` | shopping cart |
| `compare` | product comparison |
| `favorites` | user favorites |
| `images` | image processing and uploads |
| `ranking_index` | popularity index management |
| `recently_viewed` | recently viewed products |
| `search` | full-text product search |
| `short_links` | short link generation mechanism |
| `tags_importers` | automated product tag assignment via schedule |
| `telegram` | Telegram bot notifications |
| `web_pages` | SEO pages for products, catalogs, and articles |
| `blog` | articles, categories, and content management |
| `customer` | customer data and profiles |
| `utils` | shared utilities, cache, validators, formatting, etc. |

---

## 🧠 Code Quality & Standards

StoreAPI adheres to modern Python development standards:

```bash
mypy .
flake8 .
black .
isort .
```

- 100% type-hinted codebase
- Consistent formatting and import sorting
- Follows PEP-8 and DRF best practices

🧩 Additional Features
- SEO-optimized meta data for all product and catalog pages
- Ready-to-use REST endpoints for frontend integration
- Modular structure for easy scaling and feature expansion
- Docker-based setup for consistent development and production environments
