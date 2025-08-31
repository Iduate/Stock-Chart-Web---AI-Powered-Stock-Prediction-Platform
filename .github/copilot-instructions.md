# Stock Chart Web - Project Instructions

This file provides workspace-specific custom instructions for GitHub Copilot.

## Project Status

- [x] **Project Requirements Clarified**: Django backend with PostgreSQL, HTML/CSS/JavaScript frontend, stock prediction platform with multiple features
- [x] **Project Scaffolded**: Django project created with 5 apps (users, charts, payments, social_integration, loans), PostgreSQL database configured and connected, environment variables set up, all models created and migrated
- [x] **Project Customized**: User authentication with custom User model, stock chart prediction system, payment integration setup, social media integration models, cryptocurrency collateral loan system, admin panel configured, sample data populated
- [x] **Extensions Installed**: No specific extensions required for this Django project
- [x] **Project Compiled**: All dependencies installed, database migrations applied, sample data created, PostgreSQL connection established, no compilation errors
- [x] **Task Created and Run**: Development server running successfully on http://127.0.0.1:8001/, task not needed as Django handles running via manage.py runserver
- [x] **Project Launched**: Django development server running on port 8001, database populated with sample data, superuser created (davididuate11@gmail.com), ready for development and testing
- [x] **Documentation Complete**: README.md file created with comprehensive project information, copilot-instructions.md file cleaned up

## Project Overview

**Stock Chart Web** is a comprehensive AI-powered stock prediction platform built with:
- **Backend**: Django 5.2.5 with PostgreSQL
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5.3.0 and TradingView Charts
- **Features**: Real-time stock charts, AI predictions, social trading, cryptocurrency loans

## Development Status

The project is fully set up and running with:
- Django development server on port 8001
- PostgreSQL database with sample data
- 5 Django apps with complete models
- Base templates and static files
- Admin panel access

## Next Development Steps

1. **Frontend Templates**: Complete specific pages for user registration, chart viewing, predictions
2. **API Endpoints**: Implement REST API endpoints for real-time data and user interactions
3. **External Integrations**: Connect to stock data APIs, payment processors, and social media OAuth
4. **Testing**: Add comprehensive test coverage
5. **Deployment**: Prepare for production deployment

## Superuser Access

- **URL**: http://127.0.0.1:8001/admin/
- **Email**: davididuate11@gmail.com
- **Password**: Iduate

## Key Commands

- **Start Server**: `python manage.py runserver 8001`
- **Apply Migrations**: `python manage.py migrate`
- **Create Sample Data**: `python manage.py populate_data`
- **Create Superuser**: `python manage.py createsuperuser`
