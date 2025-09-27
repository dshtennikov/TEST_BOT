# bot.py
try:
text = ocr_image(local_path)
prompt = f"Пользователь прислал изображение. Распознанный текст:\n\n{text}\n\nВопрос: {update.message.caption or 'Нет явного вопроса — прокомментируй содержимое.'}"
reply = send_to_gigachat(prompt)
await update.message.reply_text(reply)
except Exception as e:
logger.exception('OCR failed')
await update.message.reply_text(f"Ошибка при OCR: {e}")




async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
doc = update.message.document
file = await context.bot.get_file(doc.file_id)
local_path = DOWNLOAD_DIR / f"{doc.file_name}"
await file.download_to_drive(custom_path=str(local_path))


if doc.mime_type == 'application/pdf' or doc.file_name.lower().endswith('.pdf'):
await update.message.reply_text("PDF получен — извлекаю текст...")
try:
text = extract_text_from_pdf(local_path)
prompt = f"Пользователь прислал PDF. Извлечённый текст:\n\n{text[:4000]}\n\nВопрос: {update.message.caption or 'Прокомментируй содержание.'}"
reply = send_to_gigachat(prompt)
await update.message.reply_text(reply)
except Exception as e:
logger.exception('PDF processing failed')
await update.message.reply_text(f"Ошибка при обработке PDF: {e}")


elif doc.mime_type in [
'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
'application/msword'] or doc.file_name.lower().endswith('.docx'):
await update.message.reply_text("DOCX получен — извлекаю текст...")
try:
text = extract_text_from_docx(local_path)
prompt = f"Пользователь прислал DOCX. Извлечённый текст:\n\n{text[:4000]}\n\nВопрос: {update.message.caption or 'Прокомментируй содержание.'}"
reply = send_to_gigachat(prompt)
await update.message.reply_text(reply)
except Exception as e:
logger.exception('DOCX processing failed')
await update.message.reply_text(f"Ошибка при обработке DOCX: {e}")


elif doc.mime_type in [
'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
'application/vnd.ms-excel'] or doc.file_name.lower().endswith('.xlsx'):
await update.message.reply_text("XLSX получен — извлекаю данные...")
try:
text = extract_text_from_xlsx(local_path)
prompt = f"Пользователь прислал XLSX. Извлечённые данные:\n\n{text[:4000]}\n\nВопрос: {update.message.caption or 'Прокомментируй данные.'}"
reply = send_to_gigachat(prompt)
await update.message.reply_text(reply)
except Exception as e:
logger.exception('XLSX processing failed')
await update.message.reply_text(f"Ошибка при обработке XLSX: {e}")
else:
await update.message.reply_text("Поддерживаются только PDF, DOCX и XLSX.")

def ocr_image(path: Path) -> str:
img = Image.open(path)
if img.mode != 'RGB':
img = img.convert('RGB')
text = pytesseract.image_to_string(img)
return text




def extract_text_from_pdf(path: Path) -> str:
doc = fitz.open(str(path))
full_text = []
need_ocr_pages = []
for page_num in range(doc.page_count):
page = doc.load_page(page_num)
text = page.get_text().strip()
if text:
full_text.append(text)
else:
need_ocr_pages.append(page_num)
if need_ocr_pages:
images = convert_from_path(str(path), first_page=min(need_ocr_pages)+1, last_page=max(need_ocr_pages)+1)
for i, page_num in enumerate(need_ocr_pages):
img = images[i]
txt = pytesseract.image_to_string(img)
full_text.append(txt)
return "\n\n---PAGE---\n\n".join(full_text)




def extract_text_from_docx(path: Path) -> str:
doc = Document(str(path))
return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])




def extract_text_from_xlsx(path: Path) -> str:
wb = openpyxl.load_workbook(str(path), data_only=True)
all_text = []
for sheet in wb.sheetnames:
ws = wb[sheet]
rows = []
for row in ws.iter_rows(values_only=True):
rows.append("\t".join([str(cell) if cell is not None else '' for cell in row]))
all_text.append(f"[Sheet: {sheet}]\n" + "\n".join(rows))
return "\n\n---SHEET---\n\n".join(all_text)




def main():
if not TELEGRAM_TOKEN or not GIGA_CHAT_TOKEN:
logger.error('TELEGRAM_TOKEN or GIGA_CHAT_TOKEN not set in environment')
print('Set TELEGRAM_TOKEN and GIGA_CHAT_TOKEN in env or .env file (see .env.example)')
return


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()


app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


logger.info('Starting bot...')
app.run_polling()




if __name__ == '__main__':
main()
