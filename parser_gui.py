import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os


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

def run_parser():
    lots = entry.get()
    if not lots:
        messagebox.showerror("Ошибка", "Введите название лота")
        return
    create_empty_excel(["Ссылка", "Тип закупки", "Дата окончания", "Лот"], "lots.xlsx")
  
    service = SafariService()
    driver = webdriver.Safari(service=service)

    for page in range(1, 4):
        url = f"https://www.goszakup.gov.kz/ru/search/lots?filter%5Bname%5D={lots}&count_record=100&page={page}"
        driver.get(url)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        try:
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search-result"))
            )
            rows = table.find_elements(By.TAG_NAME, "tr")
        except Exception as e:
            print(f"Ошибка при загрузке таблицы: {e}")
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
                    driver.get(href)
                    try:
                        end_date_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//label[contains(text(), 'окончания приема заявок')]/following-sibling::div/input")
                            )
                        )
                        end_date = end_date_input.get_attribute("value")
                        append_rows_to_excel([href, zakup_type, end_date, lots], "lots.xlsx")
                    except Exception as e:
                        print(f"Ошибка при получении даты: {e}")
                    driver.back()
            except Exception as e:
                print(f"Ошибка на строке {i} страницы {page}: {e}")
    driver.quit()
    messagebox.showinfo("Готово", "Завершено")

# GUI
root = tk.Tk()
root.title("Парсер закупок")
root.geometry("400x150")
tk.Label(root, text="Введите название лота:").pack(pady=10)
entry = tk.Entry(root, width=40)
entry.pack(pady=5)
tk.Button(root, text="Начать", command=run_parser).pack(pady=10)
root.mainloop()
