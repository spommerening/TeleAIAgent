"""
Settings Command Handler (AsyncIO)
Handler for /settings command to manage channel-specific settings
"""

import logging
from typing import Dict, Any, Optional
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from utils.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class SettingsCallbackData(CallbackData, prefix="settings", sep="|"):
    """Callback data for settings interactions using | separator to avoid conflicts with model names"""
    action: str  # 'vision_model', 'text_model', 'back', 'close'
    value: Optional[str] = None  # Model name or other value


class SettingsHandler:
    def __init__(self, bot, db_path: str = "/app/data/settings.db"):
        self.bot = bot
        self.settings_manager = SettingsManager(db_path=db_path)
    
    async def initialize(self):
        """Initialize settings manager"""
        await self.settings_manager.initialize()
        logger.info("✅ Settings handler initialized")
    
    async def handle_settings_command(self, message: types.Message):
        """Handle /settings command"""
        chat_id = message.chat.id
        chat_title = message.chat.title or message.chat.first_name or f"Chat {chat_id}"
        
        try:
            # Get current settings
            settings = await self.settings_manager.get_channel_settings(chat_id)
            
            # Create settings overview
            text = f"⚙️ **Einstellungen für {chat_title}**\n\n"
            text += f"🎯 **Vision Modell:** `{settings.vision_model}`\n"
            text += f"💬 **Text Modell:** `{settings.text_model}`\n"
            text += f"🏷️ **Auto-Tagging:** {'✅ Ein' if settings.auto_tag else '❌ Aus'}\n"
            text += f"🌍 **Sprache:** {settings.response_language.upper()}\n\n"
            text += "Wähle eine Option zum Ändern:"
            
            # Create inline keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🎯 Vision Modell ändern",
                    callback_data=SettingsCallbackData(action="vision_model").pack()
                )],
                [InlineKeyboardButton(
                    text="💬 Text Modell ändern", 
                    callback_data=SettingsCallbackData(action="text_model").pack()
                )],
                [InlineKeyboardButton(
                    text="📊 Statistiken",
                    callback_data=SettingsCallbackData(action="stats").pack()
                )],
                [InlineKeyboardButton(
                    text="❌ Schließen",
                    callback_data=SettingsCallbackData(action="close").pack()
                )]
            ])
            
            await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Error handling settings command: {e}", exc_info=True)
            await message.reply("❌ Fehler beim Laden der Einstellungen.")
    
    async def handle_settings_callback(self, callback: types.CallbackQuery):
        """Handle settings callback queries"""
        try:
            callback_data = SettingsCallbackData.unpack(callback.data)
            action = callback_data.action
            value = callback_data.value
            
            chat_id = callback.message.chat.id
            message_id = callback.message.message_id
            
            if action == "close":
                await callback.message.delete()
                await callback.answer("Einstellungen geschlossen")
                return
            
            elif action == "vision_model":
                await self._show_vision_model_selection(callback)
                return
                
            elif action == "text_model":
                await self._show_text_model_selection(callback)
                return
                
            elif action == "stats":
                await self._show_statistics(callback)
                return
            
            elif action == "set_vision_model":
                await self._set_vision_model(callback, value)
                return
                
            elif action == "set_text_model":
                await self._set_text_model(callback, value)
                return
            
            elif action == "back":
                # Go back to main settings menu
                await self._show_main_settings(callback)
                return
            
            await callback.answer("Unbekannte Aktion")
            
        except Exception as e:
            logger.error(f"❌ Error handling settings callback: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Verarbeiten der Einstellung")
    
    async def _show_vision_model_selection(self, callback: types.CallbackQuery):
        """Show vision model selection menu"""
        try:
            chat_id = callback.message.chat.id
            current_settings = await self.settings_manager.get_channel_settings(chat_id)
            available_models = await self.settings_manager.get_available_models("vision")
            
            if not available_models:
                await callback.answer("❌ Keine Vision-Modelle verfügbar")
                return
            
            text = f"🎯 **Vision Modell auswählen**\n\n"
            text += f"Aktuell: `{current_settings.vision_model}`\n\n"
            text += "Verfügbare Modelle:"
            
            # Create keyboard with available models
            keyboard_buttons = []
            for model in available_models:
                model_name = model['model_name']
                description = model.get('description', '')
                
                # Mark current model
                display_text = f"{'✅ ' if model_name == current_settings.vision_model else ''}{model_name}"
                if description:
                    display_text += f" - {description[:30]}..."
                
                keyboard_buttons.append([InlineKeyboardButton(
                    text=display_text,
                    callback_data=SettingsCallbackData(action="set_vision_model", value=model_name).pack()
                )])
            
            # Add back button
            keyboard_buttons.append([InlineKeyboardButton(
                text="🔙 Zurück",
                callback_data=SettingsCallbackData(action="back").pack()
            )])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"❌ Error showing vision model selection: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Laden der Modelle")
    
    async def _show_text_model_selection(self, callback: types.CallbackQuery):
        """Show text model selection menu"""
        try:
            chat_id = callback.message.chat.id
            current_settings = await self.settings_manager.get_channel_settings(chat_id)
            available_models = await self.settings_manager.get_available_models("text")
            
            if not available_models:
                await callback.answer("❌ Keine Text-Modelle verfügbar")
                return
            
            text = f"💬 **Text Modell auswählen**\n\n"
            text += f"Aktuell: `{current_settings.text_model}`\n\n"
            text += "Verfügbare Modelle:"
            
            # Create keyboard with available models
            keyboard_buttons = []
            for model in available_models:
                model_name = model['model_name']
                description = model.get('description', '')
                
                # Mark current model
                display_text = f"{'✅ ' if model_name == current_settings.text_model else ''}{model_name}"
                if description:
                    display_text += f" - {description[:30]}..."
                
                keyboard_buttons.append([InlineKeyboardButton(
                    text=display_text,
                    callback_data=SettingsCallbackData(action="set_text_model", value=model_name).pack()
                )])
            
            # Add back button
            keyboard_buttons.append([InlineKeyboardButton(
                text="🔙 Zurück",
                callback_data=SettingsCallbackData(action="back").pack()
            )])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"❌ Error showing text model selection: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Laden der Modelle")
    
    async def _set_vision_model(self, callback: types.CallbackQuery, model_name: Optional[str]):
        """Set vision model for channel"""
        try:
            if not model_name:
                await callback.answer("❌ Kein Modell angegeben")
                return
                
            chat_id = callback.message.chat.id
            chat_title = callback.message.chat.title or callback.message.chat.first_name or f"Chat {chat_id}"
            
            success = await self.settings_manager.set_vision_model(chat_id, model_name, chat_title)
            
            if success:
                await callback.answer(f"✅ Vision Modell geändert zu: {model_name}")
                await self._show_main_settings(callback)
                logger.info(f"✅ Changed vision model for chat {chat_id} to {model_name}")
            else:
                await callback.answer("❌ Fehler beim Speichern der Einstellung")
                
        except Exception as e:
            logger.error(f"❌ Error setting vision model: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Speichern der Einstellung")
    
    async def _set_text_model(self, callback: types.CallbackQuery, model_name: Optional[str]):
        """Set text model for channel"""
        try:
            if not model_name:
                await callback.answer("❌ Kein Modell angegeben")
                return
                
            chat_id = callback.message.chat.id
            chat_title = callback.message.chat.title or callback.message.chat.first_name or f"Chat {chat_id}"
            
            success = await self.settings_manager.set_text_model(chat_id, model_name, chat_title)
            
            if success:
                await callback.answer(f"✅ Text Modell geändert zu: {model_name}")
                await self._show_main_settings(callback)
                logger.info(f"✅ Changed text model for chat {chat_id} to {model_name}")
            else:
                await callback.answer("❌ Fehler beim Speichern der Einstellung")
                
        except Exception as e:
            logger.error(f"❌ Error setting text model: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Speichern der Einstellung")
    
    async def _show_statistics(self, callback: types.CallbackQuery):
        """Show database statistics"""
        try:
            stats = await self.settings_manager.get_statistics()
            
            text = "📊 **Einstellungen Statistiken**\n\n"
            text += f"📊 Konfigurierte Kanäle: {stats.get('total_channels', 0)}\n\n"
            
            # Vision model usage
            vision_usage = stats.get('vision_model_usage', [])
            if vision_usage:
                text += "🎯 **Vision Modell Nutzung:**\n"
                for usage in vision_usage[:5]:  # Top 5
                    text += f"• `{usage['vision_model']}`: {usage['count']} Kanäle\n"
                text += "\n"
            
            # Text model usage
            text_usage = stats.get('text_model_usage', [])
            if text_usage:
                text += "💬 **Text Modell Nutzung:**\n"
                for usage in text_usage[:5]:  # Top 5
                    text += f"• `{usage['text_model']}`: {usage['count']} Kanäle\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔙 Zurück",
                    callback_data=SettingsCallbackData(action="back").pack()
                )]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"❌ Error showing statistics: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Laden der Statistiken")
    
    async def _show_main_settings(self, callback: types.CallbackQuery):
        """Show main settings menu"""
        try:
            chat_id = callback.message.chat.id
            chat_title = callback.message.chat.title or callback.message.chat.first_name or f"Chat {chat_id}"
            
            # Get current settings
            settings = await self.settings_manager.get_channel_settings(chat_id)
            
            # Create settings overview
            text = f"⚙️ **Einstellungen für {chat_title}**\n\n"
            text += f"🎯 **Vision Modell:** `{settings.vision_model}`\n"
            text += f"💬 **Text Modell:** `{settings.text_model}`\n"
            text += f"🏷️ **Auto-Tagging:** {'✅ Ein' if settings.auto_tag else '❌ Aus'}\n"
            text += f"🌍 **Sprache:** {settings.response_language.upper()}\n\n"
            text += "Wähle eine Option zum Ändern:"
            
            # Create inline keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🎯 Vision Modell ändern",
                    callback_data=SettingsCallbackData(action="vision_model").pack()
                )],
                [InlineKeyboardButton(
                    text="💬 Text Modell ändern", 
                    callback_data=SettingsCallbackData(action="text_model").pack()
                )],
                [InlineKeyboardButton(
                    text="📊 Statistiken",
                    callback_data=SettingsCallbackData(action="stats").pack()
                )],
                [InlineKeyboardButton(
                    text="❌ Schließen",
                    callback_data=SettingsCallbackData(action="close").pack()
                )]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"❌ Error showing main settings: {e}", exc_info=True)
            await callback.answer("❌ Fehler beim Laden der Einstellungen")