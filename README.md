# LearnStack LMS Backend

> A professional, modular, and scalable multi-tenant Learning Management System (LMS) SaaS platform built with Django REST Framework.

## 📋 Overview

LearnStack Backend is a comprehensive LMS platform designed to serve multiple tenants (organizations) with isolated data, users, courses, assessments, analytics, and communications. The project follows best practices for modularity, maintainability, and Test-Driven Development (TDD).

### Key Features

- **Multi-Tenancy**: Complete tenant isolation across all data and operations
- **Modular Architecture**: Six core modules as independent Django apps
- **RESTful API**: DRF-powered API for Vue.js SPA frontend
- **Role-Based Access Control**: Tenant-aware permissions (Admin, Instructor, Student)
- **Test-Driven Development**: Comprehensive test coverage with pytest and factory_boy
- **Async Task Processing**: Celery integration for notifications, grading, and analytics
- **Production-Ready**: Docker containerization and CI/CD ready

## 🏗️ Architecture & Development Approach

### Core Modules

We will build the platform module by module, following TDD principles:

1. **Users & Role Management** - Multi-tenant user authentication and role-based access
2. **Courses & Content Management** - Course creation, lessons, categories, and tags
3. **Assessments & Quizzes** - Quiz creation, submissions, and grading
4. **Certifications & Achievements** - Certificate generation and badge system
5. **Analytics & Reporting** - Progress tracking and completion statistics
6. **Communications & Collaboration** - Messaging, threads, and notifications

### Project Structure

```
LearnStack-Backend/
├── lms_project/                # Core Django settings
│   ├── __init__.py
│   ├── settings.py            # Django & DRF configuration
│   ├── urls.py                # Root URL routing
│   ├── wsgi.py                # WSGI application
│   ├── asgi.py                # ASGI for async support
│   └── celery.py              # Celery configuration
│
├── modules/                    # Modular app architecture
│   └── users/                 # User & Role Management Module
│       ├── models.py          # Database schema
│       ├── serializers.py     # DTOs for API
│       ├── views.py           # API endpoints
│       ├── services.py        # Business logic
│       ├── permissions.py     # Access control
│       ├── factories.py       # Test data factories
│       ├── urls.py            # Module routes
│       └── tests/             # Unit & integration tests
│           ├── test_models.py
│           ├── test_serializers.py
│           └── test_views.py
│
├── docker/                     # Docker configuration
├── manage.py                  # Django management
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Test configuration
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Multi-container orchestration
└── .env.example              # Environment template
```

### Module Code Structure

Each module follows this pattern:

- **models.py** - Database schema with tenant associations
- **serializers.py** - Input validation and output formatting (DTOs)
- **views.py** - API endpoints (ViewSets/APIViews as controllers)
- **services.py** - Business logic layer (tenant-aware)
- **permissions.py** - Role-based access control
- **factories.py** - Test data generation with factory_boy
- **urls.py** - Module-specific routing
- **tests/** - Unit and integration tests

## 🔒 Multi-Tenancy Strategy

The platform implements **row-level multi-tenancy** where:

- Each tenant (organization) has isolated data via foreign key relationships
- Tenant context is automatically applied to all queries through middleware
- Role-based permissions are tenant-aware and enforced at the API level
- Users can only access data within their assigned tenant

**Implementation Approach:**
1. Every model includes a `tenant` foreign key field
2. Custom middleware extracts tenant context from JWT token or request headers
3. QuerySet filters automatically inject tenant conditions
4. Services layer validates tenant ownership before any data mutation

## 🛠️ Development Approach

### Test-Driven Development (TDD)

We follow a strict TDD workflow for all features:

1. **Write Failing Test**: Define expected behavior through unit/integration tests
2. **Implement Minimum Code**: Write just enough code to make the test pass
3. **Refactor**: Clean up code while keeping tests green
4. **Commit**: Push tested, working code to repository
5. **Repeat**: Continue with next feature or test case

### Module Development Sequence

We will build modules in this order:

1. **Core Tenant Model** → Establish multi-tenancy foundation
2. **Users & Roles** → Authentication, authorization, and user management
3. **Courses** → Course catalog, lessons, and content organization
4. **Assessments** → Quizzes, assignments, and grading system
5. **Certifications** → Certificate generation and achievement tracking
6. **Analytics** → Dashboards, reports, and progress tracking
7. **Communications** → Messaging, notifications, and collaboration

### Development Best Practices

- **Service Layer Separation**: All business logic lives in `services.py`, not in views
- **Serializers as DTOs**: Input validation and output formatting only - no business logic
- **Tenant-Aware Queries**: Every database query automatically filters by tenant
- **Permission-First**: Apply role-based permissions to every API endpoint
- **Factory Fixtures**: Use factory_boy for generating consistent test data
- **Code Quality**: Follow PEP 8, use type hints, write comprehensive docstrings

### Code Quality Standards

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
pylint modules/
```

## 📦 Technology Stack

- **Django 5.0+** - Web framework with ORM
- **Django REST Framework 3.14+** - RESTful API toolkit
- **MySQL 8.0+** - Relational database
- **Celery 5.3+** - Asynchronous task queue
- **Redis 7.0+** - Celery broker and caching
- **pytest + factory_boy** - Testing framework
- **Docker** - Containerization

---

**Version:** 1.0.0  
**Last Updated:** January 20, 2026  
**Django Version:** 5.0+  
**Python Version:** 3.11+
