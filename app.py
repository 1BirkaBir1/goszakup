from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'secret-key'  # Для flash-сообщений

def create_empty_excel(columns: list, filename: str, sheet_name: str = 'Sheet1') -> str:
    output_dir = 'excel_files'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        return filepath
    df = pd.DataFrame(columns=columns)
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name, freeze_panes=(1, 0))
    return filepath

def append_rows_to_excel(row: list[str], filename: str, sheet_name: str = 'Sheet1'):
    filepath = os.path.join('excel_files', filename)
    if os.path.exists(filepath):
        df_existing = pd.read_excel(filepath, sheet_name=sheet_name)
        columns = df_existing.columns.tolist()
    else:
        raise FileNotFoundError(f"{filename} does not exist.")
    if len(row) != len(columns):
        raise ValueError(f"Row has {len(row)} elements, expected {len(columns)}.")
    if row in df_existing.values.tolist():
        return
    df_new = pd.DataFrame([row], columns=columns)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        df_combined.to_excel(writer, index=False, sheet_name=sheet_name, freeze_panes=(1, 0))

def parse_lots(lots: str):
    create_empty_excel(["Ссылка", "Тип закупки", "Дата окончания", "Лот"], "lots.xlsx")

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        for page in range(1, 4):
            url = f"https://www.goszakup.gov.kz/ru/search/lots?filter%5Bname%5D={lots}&count_record=100&page={page}"
            driver.get(url)
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            try:
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search-result"))
                )
                rows = table.find_elements(By.TAG_NAME, "tr")
            except Exception:
                continue

            for i in range(1, len(rows)):
                try:
                    td = rows[i].find_element(By.XPATH, "./td[2]")
                    link = td.find_element(By.TAG_NAME, "a")
                    href = link.get_attribute("href")
                    columns = rows[i].find_elements(By.TAG_NAME, "td")
                    column_data = [col.text for col in columns]
                    zakup_type = column_data[5]
                    status = column_data[6]
                    if zakup_type != "Из одного источника по несостоявшимся закупкам" and \
                       status in ["Опубликован", "Опубликован (прием заявок)", "Опубликован (прием ценовых предложений)"]:
                        driver.execute_script("window.open(arguments[0]);", href)
                        driver.switch_to.window(driver.window_handles[1])
                        try:
                            end_date_input = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//label[contains(text(), 'окончания приема заявок')]/following-sibling::div/input")
                                )
                            )
                            end_date = end_date_input.get_attribute("value")
                            append_rows_to_excel([href, zakup_type, end_date, lots], "lots.xlsx")
                        except Exception:
                            pass
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    continue
    finally:
        driver.quit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        lot_name = request.form.get("lot_name")
        if not lot_name:
            flash("Введите название лота!", "danger")
            return redirect(url_for('index'))
        parse_lots(lot_name)
        flash("Парсинг завершён! Вы можете скачать файл ниже.", "success")
        return redirect(url_for('index'))
    return render_template("index.html")

@app.route("/download")
def download_file():
    filepath = os.path.join('excel_files', 'lots.xlsx')
    return send_from_directory('excel_files', 'lots.xlsx', as_attachment=True)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

