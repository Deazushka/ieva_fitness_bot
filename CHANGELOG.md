# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-21

### Added
- Initial release
- FSM-based conversation flow using ConversationHandler
- Inline keyboard navigation with CallbackQueryHandler
- Workout tracking with categories and exercises
- Input validation for sets/reps/weight (multiple formats)
- Workout history with pagination
- User settings (language, units, notifications)
- SQLite database with 5 tables
- Multi-language support (RU/EN)
- Comprehensive README with examples
- Environment variables configuration via .env
- Error handling and logging

### Features
- Start/finish workout functionality
- Add/delete categories and exercises during workout
- View workout history with details
- Detailed workout summaries
- User preferences management (language, units)
- Cancel active workout

### Database Tables
- categories - workout categories
- exercises - exercise library
- workouts - workout sessions with timestamps
- workout_exercises - exercises performed in each workout
- user_settings - user preferences

### Commands
- /start - Main menu
- /help - Help information
- /history - Workout history
- /settings - User settings
- /cancel - Cancel current action
