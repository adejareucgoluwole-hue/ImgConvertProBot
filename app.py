import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from io import BytesIO
from PIL import Image
import requests

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required!")

# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = (
        f"🖼️ **Welcome {user.first_name}!**\n\n"
        "I'm **ImgConvertProBot** - your professional image conversion assistant!\n\n"
        "📸 **What I can do:**\n"
        "• Convert images between formats\n"
        "• Compress images to save space\n"
        "• Resize images to any dimensions\n\n"
        "✨ **Supported formats:**\n"
        "JPG, PNG, WebP, BMP, GIF\n\n"
        "🚀 **How to use:**\n"
        "1. Send me any image\n"
        "2. Choose what you want to do\n"
        "3. Get your converted image instantly!\n\n"
        "Just send me an image to get started! 💫"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when /help is issued."""
    help_text = (
        "📋 **ImgConvertProBot Help**\n\n"
        "**Commands:**\n"
        "/start - Welcome message\n"
        "/help - This help message\n"
        "/about - About this bot\n"
        "/compress - Compress the last image\n"
        "/resize WIDTH HEIGHT - Resize image\n"
        "/info - Get image information\n\n"
        "**How to use:**\n"
        "1️⃣ Send an image (photo or file)\n"
        "2️⃣ Click a conversion button\n"
        "3️⃣ Get your converted image!\n\n"
        "**Tips:**\n"
        "• Send multiple images for batch conversion\n"
        "• Use /compress to reduce file size\n"
        "• Use /resize to change dimensions"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about info."""
    about_text = (
        "🖼️ **ImgConvertProBot v2.0**\n\n"
        "A professional image format converter bot for Telegram.\n\n"
        "🔧 **Features:**\n"
        "• Convert between 5+ formats\n"
        "• Smart compression\n"
        "• Custom resizing\n"
        "• Batch conversion\n"
        "• Fast & reliable\n\n"
        "📝 **Tech Stack:**\n"
        "• Python 3.12\n"
        "• python-telegram-bot\n"
        "• Pillow (PIL)\n"
        "• Deployed on Railway\n\n"
        "👨‍💻 Built with ❤️ for the Telegram community"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get information about the last image."""
    if 'last_image' not in context.user_data:
        await update.message.reply_text(
            "❌ No image found!\n\n"
            "Please send me an image first, then use /info."
        )
        return
    
    image_bytes = context.user_data['last_image']
    image = Image.open(BytesIO(image_bytes))
    
    width, height = image.size
    file_size = len(image_bytes) // 1024
    format_name = image.format or 'Unknown'
    mode = image.mode
    
    info_text = (
        f"📊 **Image Information**\n\n"
        f"📐 Dimensions: {width}×{height} pixels\n"
        f"📊 File size: {file_size} KB\n"
        f"🔷 Format: {format_name}\n"
        f"🎨 Color mode: {mode}\n"
        f"📁 Aspect ratio: {width/height:.2f}:1"
    )
    
    await update.message.reply_text(info_text, parse_mode="Markdown")

async def compress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compress the last image."""
    if 'last_image' not in context.user_data:
        await update.message.reply_text(
            "❌ No image found!\n\n"
            "Please send me an image first, then use /compress."
        )
        return
    
    image_bytes = context.user_data['last_image']
    image = Image.open(BytesIO(image_bytes))
    
    await update.message.reply_text("📦 Compressing image... Please wait ⏳")
    
    try:
        output = BytesIO()
        original_format = image.format or 'JPEG'
        
        if original_format in ['PNG', 'GIF']:
            image.save(output, format=original_format, optimize=True)
        else:
            image.save(output, format='JPEG', quality=60, optimize=True)
        
        output.seek(0)
        
        original_size = len(image_bytes)
        compressed_size = output.getbuffer().nbytes
        reduction = ((original_size - compressed_size) / original_size) * 100
        
        await update.message.reply_document(
            document=output,
            filename=f"compressed.{original_format.lower()}",
            caption=(
                f"✅ **Compressed!**\n\n"
                f"📊 Original: {original_size//1024}KB\n"
                f"📊 Compressed: {compressed_size//1024}KB\n"
                f"📉 Reduction: {reduction:.1f}%\n"
                f"🔷 Format: {original_format}"
            )
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error compressing image: {str(e)}")

async def resize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resize the last image."""
    if 'last_image' not in context.user_data:
        await update.message.reply_text(
            "❌ No image found!\n\n"
            "Please send me an image first, then use /resize."
        )
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📏 **Resize Tool**\n\n"
            "Usage: `/resize WIDTH HEIGHT`\n\n"
            "Example: `/resize 800 600`\n\n"
            "⚠️ The image will be resized to these exact dimensions."
        )
        return
    
    try:
        width = int(context.args[0])
        height = int(context.args[1])
        
        if width <= 0 or height <= 0:
            await update.message.reply_text("❌ Width and height must be positive numbers!")
            return
        
        if width > 4000 or height > 4000:
            await update.message.reply_text("❌ Maximum dimensions are 4000x4000 pixels!")
            return
        
    except ValueError:
        await update.message.reply_text("❌ Please provide valid numbers for width and height.")
        return
    
    image_bytes = context.user_data['last_image']
    image = Image.open(BytesIO(image_bytes))
    original_format = image.format or 'JPEG'
    
    await update.message.reply_text(f"📐 Resizing to {width}x{height}... ⏳")
    
    try:
        resized = image.resize((width, height), Image.Resampling.LANCZOS)
        
        output = BytesIO()
        resized.save(output, format=original_format)
        output.seek(0)
        
        await update.message.reply_document(
            document=output,
            filename=f"resized_{width}x{height}.{original_format.lower()}",
            caption=(
                f"✅ **Resized!**\n\n"
                f"📐 New dimensions: {width}x{height}\n"
                f"🔷 Format: {original_format}"
            )
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error resizing image: {str(e)}")

# ============= IMAGE HANDLERS =============

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages - show conversion options."""
    photo = update.message.photo[-1]  # Get the largest photo
    file = await photo.get_file()
    
    # Download the image
    image_bytes = await file.download_as_bytearray()
    
    # Store the image in user_data for later use
    context.user_data['last_image'] = image_bytes
    
    # Get image info
    image = Image.open(BytesIO(image_bytes))
    width, height = image.size
    file_size = len(image_bytes) // 1024  # KB
    current_format = image.format or 'Unknown'
    
    # Create inline keyboard with format options
    keyboard = [
        [
            InlineKeyboardButton("🔄 JPG", callback_data="convert_jpg"),
            InlineKeyboardButton("🔄 PNG", callback_data="convert_png"),
            InlineKeyboardButton("🔄 WebP", callback_data="convert_webp"),
        ],
        [
            InlineKeyboardButton("🔄 BMP", callback_data="convert_bmp"),
            InlineKeyboardButton("🔄 GIF", callback_data="convert_gif"),
        ],
        [
            InlineKeyboardButton("📦 Compress", callback_data="compress_quick"),
            InlineKeyboardButton("ℹ️ Info", callback_data="info"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📸 **Image Received!**\n\n"
        f"📐 Size: {width}x{height}\n"
        f"📊 File: {file_size}KB\n"
        f"🔷 Format: {current_format}\n\n"
        f"**Choose an option below:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document messages (images sent as files)."""
    document = update.message.document
    
    # Check if it's an image
    mime_type = document.mime_type or ''
    file_name = document.file_name or ''
    
    if mime_type.startswith('image/') or file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
        file = await document.get_file()
        image_bytes = await file.download_as_bytearray()
        context.user_data['last_image'] = image_bytes
        
        # Show the same conversion options
        keyboard = [
            [
                InlineKeyboardButton("🔄 JPG", callback_data="convert_jpg"),
                InlineKeyboardButton("🔄 PNG", callback_data="convert_png"),
                InlineKeyboardButton("🔄 WebP", callback_data="convert_webp"),
            ],
            [
                InlineKeyboardButton("🔄 BMP", callback_data="convert_bmp"),
                InlineKeyboardButton("🔄 GIF", callback_data="convert_gif"),
            ],
            [
                InlineKeyboardButton("📦 Compress", callback_data="compress_quick"),
                InlineKeyboardButton("ℹ️ Info", callback_data="info"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📸 **Image Received!**\n\n"
            f"📁 Name: {file_name}\n"
            f"📊 Size: {len(image_bytes)//1024}KB\n\n"
            f"**Choose an option below:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"⚠️ I can only process images.\n\n"
            f"Please send me a JPG, PNG, GIF, WebP, or BMP file."
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages that aren't commands."""
    text = update.message.text
    word_count = len(text.split())
    char_count = len(text)
    
    await update.message.reply_text(
        f"📝 **Message received!**\n\n"
        f"Word count: {word_count}\n"
        f"Character count: {char_count}\n\n"
        f"Try sending me an image or using /help to see available commands."
    )

# ============= CALLBACK QUERY HANDLERS =============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses for image conversion."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    user_data = context.user_data
    
    if action == "cancel":
        await query.edit_message_text("❌ Operation cancelled.")
        return
    
    if action == "info":
        if 'last_image' not in user_data:
            await query.edit_message_text("❌ No image found. Please send a new image.")
            return
        
        image_bytes = user_data['last_image']
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
        file_size = len(image_bytes) // 1024
        format_name = image.format or 'Unknown'
        mode = image.mode
        
        info_text = (
            f"📊 **Image Information**\n\n"
            f"📐 Dimensions: {width}×{height} pixels\n"
            f"📊 File size: {file_size} KB\n"
            f"🔷 Format: {format_name}\n"
            f"🎨 Color mode: {mode}\n"
            f"📁 Aspect ratio: {width/height:.2f}:1"
        )
        
        await query.edit_message_text(info_text, parse_mode="Markdown")
        return
    
    if 'last_image' not in user_data:
        await query.edit_message_text("❌ No image found. Please send a new image.")
        return
    
    image_bytes = user_data['last_image']
    image = Image.open(BytesIO(image_bytes))
    
    try:
        output = BytesIO()
        format_name = ""
        
        if action == "convert_jpg":
            format_name = "JPG"
            # Convert to RGB if needed (JPG doesn't support alpha)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            image.save(output, format='JPEG', quality=95)
            filename = "converted.jpg"
            
        elif action == "convert_png":
            format_name = "PNG"
            image.save(output, format='PNG')
            filename = "converted.png"
            
        elif action == "convert_webp":
            format_name = "WebP"
            image.save(output, format='WEBP', quality=90)
            filename = "converted.webp"
            
        elif action == "convert_bmp":
            format_name = "BMP"
            image.save(output, format='BMP')
            filename = "converted.bmp"
            
        elif action == "convert_gif":
            format_name = "GIF"
            image.save(output, format='GIF')
            filename = "converted.gif"
            
        elif action == "compress_quick":
            format_name = "Compressed"
            original_format = image.format or 'JPEG'
            if original_format in ['PNG', 'GIF']:
                image.save(output, format=original_format, optimize=True)
            else:
                image.save(output, format='JPEG', quality=60, optimize=True)
            filename = f"compressed.{original_format.lower()}"
            
        else:
            await query.edit_message_text("❌ Unknown action.")
            return
        
        output.seek(0)
        
        # Update the message
        await query.edit_message_text(
            f"✅ **Converted to {format_name}!**\n\n"
            f"📦 Sending your image..."
        )
        
        # Send the converted image
        await query.message.reply_document(
            document=output,
            filename=filename,
            caption=f"🔄 Here's your converted image! (Format: {format_name})"
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Error processing image: {str(e)}")
    
    # Clean up
    user_data.pop('last_image', None)

# ============= MAIN APPLICATION =============

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("compress", compress_command))
    application.add_handler(CommandHandler("resize", resize_command))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    print("=" * 50)
    print("🖼️ ImgConvertProBot is starting...")
    print("🤖 Bot is now running!")
    print("ℹ️ Using polling mode - no webhook needed")
    print("📊 Ready to convert images!")
    print("=" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
