import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import ConversationState, CallbackData, MESSAGES


class TestConversationState:
    def test_main_menu_state(self):
        assert ConversationState.MAIN_MENU == 0
    
    def test_category_select_state(self):
        assert ConversationState.CATEGORY_SELECT == 2
    
    def test_exercise_select_state(self):
        assert ConversationState.EXERCISE_SELECT == 3
    
    def test_end_state(self):
        assert ConversationState.END == -1


class TestCallbackData:
    def test_start_workout(self):
        assert CallbackData.START_WORKOUT == "start_workout"
    
    def test_history(self):
        assert CallbackData.HISTORY == "history"
    
    def test_settings(self):
        assert CallbackData.SETTINGS == "settings"
    
    def test_category_prefix(self):
        assert CallbackData.CATEGORY_PREFIX == "cat_"
    
    def test_exercise_prefix(self):
        assert CallbackData.EXERCISE_PREFIX == "ex_"
    
    def test_back(self):
        assert CallbackData.BACK == "back"


class TestMessages:
    def test_messages_has_russian(self):
        assert 'ru' in MESSAGES
    
    def test_messages_has_english(self):
        assert 'en' in MESSAGES
    
    def test_start_message_ru(self):
        assert 'Добро пожаловать' in MESSAGES['ru']['start']
    
    def test_start_message_en(self):
        assert 'Welcome' in MESSAGES['en']['start']
    
    def test_help_message_ru(self):
        assert '/start' in MESSAGES['ru']['help']
    
    def test_help_message_en(self):
        assert '/start' in MESSAGES['en']['help']
    
    def test_workout_started_ru(self):
        assert 'Тренировка начата' in MESSAGES['ru']['workout_started']
    
    def test_workout_started_en(self):
        assert 'Workout started' in MESSAGES['en']['workout_started']
    
    def test_all_keys_present_in_both_languages(self):
        ru_keys = set(MESSAGES['ru'].keys())
        en_keys = set(MESSAGES['en'].keys())
        assert ru_keys == en_keys, f"Missing keys: {ru_keys ^ en_keys}"
