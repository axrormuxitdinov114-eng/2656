from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import CATEGORIES

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="🔥 New Arrivals")],
        [KeyboardButton(text="🎲 Random Pick"), KeyboardButton(text="💸 Budget & Deals")],
        [KeyboardButton(text="⭐️ Premium Collection"), KeyboardButton(text="🛍 All Categories")],
        [KeyboardButton(text="🛒 Shopping Cart"), KeyboardButton(text="📞 Contact Admin")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_category_keyboard():
    buttons = []
    for category in CATEGORIES:
        buttons.append([InlineKeyboardButton(text=category, callback_data=f"category_{category}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_action_keyboard(product_id: int, in_cart: bool = False):
    buttons = []
    if in_cart:
        buttons.append([InlineKeyboardButton(text="🛒 Remove from Cart", callback_data=f"remove_cart_{product_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🛒 Add to Cart", callback_data=f"add_cart_{product_id}")])
    buttons.append([InlineKeyboardButton(text="💰 Buy Now", callback_data=f"buy_now_{product_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="➕ Add Product", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="🗑 Delete Product", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📦 View Orders", callback_data="admin_view_orders")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_contact_keyboard():
    button = KeyboardButton(text="📱 Share Phone", request_contact=True)
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True)

def get_cart_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🛍 Continue", callback_data="back_to_menu")],
        [InlineKeyboardButton(text="🔄 Clear Cart", callback_data="clear_cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_order_confirmation_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)