from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database import db
from states import AddProductStates, OrderStates, BroadcastStates
from keyboards import (
    get_main_menu_keyboard, get_category_keyboard, 
    get_product_action_keyboard, get_admin_keyboard,
    get_contact_keyboard, get_cart_keyboard,
    get_order_confirmation_keyboard
)
from config import ADMIN_ID, CATEGORIES

router = Router()

# ============ 1-QISM: COMMANDS & MAIN MENU ============

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    await message.answer(
        f"👋 Welcome {message.from_user.first_name}!\nUse buttons below:",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Unauthorized!")
        return
    await message.answer("👑 Admin Panel:", reply_markup=get_admin_keyboard())

@router.message(F.text == "🔥 New Arrivals")
async def show_new_arrivals(message: Message):
    products = await db.get_all_products(limit=10)
    if not products:
        await message.answer("📭 No products!")
        return
    for p in products:
        await send_product_message(message, p)

@router.message(F.text == "🎲 Random Pick")
async def random_pick(message: Message):
    product = await db.get_random_product()
    if not product:
        await message.answer("📭 No products!")
        return
    await send_product_message(message, product)

@router.message(F.text == "💸 Budget & Deals")
async def show_budget_deals(message: Message):
    products = await db.get_lowest_priced_products(limit=10)
    if not products:
        await message.answer("📭 No products!")
        return
    for p in products:
        await send_product_message(message, p)

@router.message(F.text == "⭐️ Premium Collection")
async def show_premium_collection(message: Message):
    products = await db.get_premium_products()
    if not products:
        await message.answer("📭 No premium products!")
        return
    for p in products:
        await send_product_message(message, p)

@router.message(F.text == "🛍 All Categories")
async def show_categories(message: Message):
    await message.answer("📂 Select category:", reply_markup=get_category_keyboard())

@router.message(F.text == "🛒 Shopping Cart")
async def show_cart(message: Message):
    items = await db.get_cart(message.from_user.id)
    if not items:
        await message.answer("🛒 Cart is empty!")
        return
    total = 0
    text = "🛒 Your Cart:\n\n"
    for item in items:
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"📦 {item['title']} x{item['quantity']} = ${item_total:.2f}\n"
    text += f"\n💰 Total: ${total:.2f}"
    await message.answer(text, reply_markup=get_cart_keyboard())

@router.message(F.text == "📞 Contact Admin")
async def contact_admin(message: Message):
    await message.answer("📞 Contact: support@store.com")

# ============ 2-QISM: CATEGORIES & CART ============

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    category = callback.data.replace("category_", "")
    products = await db.get_products_by_category(category)
    if not products:
        await callback.message.edit_text(f"📭 No products in {category}")
        await callback.answer()
        return
    await callback.message.edit_text(f"📂 {category}:")
    for p in products:
        await send_product_message(callback.message, p)
    await callback.answer()

@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.replace("add_cart_", ""))
    await db.add_to_cart(callback.from_user.id, product_id)
    await callback.answer("✅ Added to cart!", show_alert=True)

@router.callback_query(F.data.startswith("remove_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    product_id = int(callback.data.replace("remove_cart_", ""))
    await db.remove_from_cart(callback.from_user.id, product_id)
    await callback.answer("❌ Removed!", show_alert=True)

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    await db.clear_cart(callback.from_user.id)
    await callback.message.edit_text("🛒 Cart cleared!")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_now_"))
async def buy_now(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.replace("buy_now_", ""))
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("❌ Not found!", show_alert=True)
        return
    await state.update_data(product_id=product_id)
    await state.set_state(OrderStates.waiting_for_phone)
    await callback.message.answer(
        f"📦 {product['title']}\n💰 ${product['price']:.2f}\n\nShare phone:",
        reply_markup=get_contact_keyboard()
    )
    await callback.answer()

# ============ 3-QISM: ORDER PROCESSING ============

@router.message(OrderStates.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderStates.waiting_for_address)
    await message.answer(
        "📝 Enter delivery address:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Send Location", request_location=True)]],
            resize_keyboard=True
        )
    )

@router.message(OrderStates.waiting_for_address, F.text)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    product = await db.get_product(data['product_id'])
    if not product:
        await message.answer("❌ Product not found!")
        await state.clear()
        return
    await message.answer(
        f"📋 Confirm:\n📦 {product['title']}\n💰 ${product['price']:.2f}\n📱 {data['phone']}\n📍 {data['address']}\n\nConfirm?",
        reply_markup=get_order_confirmation_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_confirmation)

@router.callback_query(OrderStates.waiting_for_confirmation, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user(callback.from_user.id)
    product = await db.get_product(data['product_id'])
    if not product:
        await callback.message.edit_text("❌ Error!")
        await state.clear()
        return
    order_id = await db.create_order(
        user_id=callback.from_user.id,
        product_id=data['product_id'],
        quantity=1,
        total_price=product['price'],
        customer_name=user['first_name'],
        phone_number=data['phone'],
        delivery_address=data['address']
    )
    await db.remove_from_cart(callback.from_user.id, data['product_id'])
    await callback.message.edit_text(f"✅ Order #{order_id} confirmed!")
    await state.clear()
    await callback.answer()

@router.callback_query(OrderStates.waiting_for_confirmation, F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Cancelled.")
    await callback.answer()

# ============ 4-QISM: ADMIN & NAVIGATION ============

@router.callback_query(F.data == "admin_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️", show_alert=True)
        return
    await state.set_state(AddProductStates.waiting_for_photo)
    await callback.message.edit_text("📸 Send photo:")
    await callback.answer()

@router.message(AddProductStates.waiting_for_photo, F.photo)
async def admin_add_photo(message: Message, state: FSMContext):
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(AddProductStates.waiting_for_title)
    await message.answer("📝 Enter title:")

@router.message(AddProductStates.waiting_for_title, F.text)
async def admin_add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddProductStates.waiting_for_description)
    await message.answer("📝 Enter description:")

@router.message(AddProductStates.waiting_for_description, F.text)
async def admin_add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProductStates.waiting_for_price)
    await message.answer("💰 Enter price:")

@router.message(AddProductStates.waiting_for_price, F.text)
async def admin_add_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AddProductStates.waiting_for_category)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"set_category_{cat}")]
            for cat in CATEGORIES
        ])
        await message.answer("📂 Select category:", reply_markup=keyboard)
    except:
        await message.answer("⚠️ Enter valid number!")

@router.callback_query(AddProductStates.waiting_for_category, F.data.startswith("set_category_"))
async def admin_set_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("set_category_", "")
    data = await state.get_data()
    product_id = await db.add_product(
        title=data['title'],
        description=data['description'],
        price=data['price'],
        category=category,
        photo_file_id=data['photo_file_id'],
        is_premium=(category == "Premium")
    )
    await callback.message.edit_text(f"✅ Product #{product_id} added!")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️", show_alert=True)
        return
    products = await db.get_all_products()
    if not products:
        await callback.message.edit_text("📭 No products!")
        await callback.answer()
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {p['title']}", callback_data=f"delete_prod_{p['id']}")]
        for p in products[:10]
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")])
    await callback.message.edit_text("🗑 Select:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("delete_prod_"))
async def confirm_delete(callback: CallbackQuery):
    product_id = int(callback.data.replace("delete_prod_", ""))
    await db.delete_product(product_id)
    await callback.message.edit_text("✅ Deleted!")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️", show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text("📢 Send message to broadcast:")
    await callback.answer()

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    users = await db.get_all_users()
    success = 0
    for user in users:
        try:
            await message.copy_to(chat_id=user['user_id'])
            success += 1
        except:
            pass
    await message.answer(f"✅ Sent to {success} users!")
    await state.clear()

@router.callback_query(F.data == "admin_view_orders")
async def admin_view_orders(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️", show_alert=True)
        return
    orders = await db.get_all_orders()
    if not orders:
        await callback.message.edit_text("📭 No orders!")
        await callback.answer()
        return
    text = "📦 Orders:\n\n"
    for o in orders[:5]:
        text += f"#{o['id']} - {o['first_name']} - ${o['total_price']}\n"
    await callback.message.edit_text(text)
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("🔙 Menu:", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# ============ HELPER ============

async def send_product_message(message: Message, product: dict):
    cart = await db.get_cart(message.from_user.id)
    in_cart = any(item['product_id'] == product['id'] for item in cart)
    text = f"📦 {product['title']}\n💰 ${product['price']:.2f}\n📂 {product['category']}"
    if product['photo_file_id']:
        await message.answer_photo(
            photo=product['photo_file_id'],
            caption=text,
            reply_markup=get_product_action_keyboard(product['id'], in_cart)
        )
    else:
        await message.answer(text, reply_markup=get_product_action_keyboard(product['id'], in_cart))