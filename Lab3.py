import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

# МОДЕЛЬ НЕЧІТКОЇ БАЗИ ЗНАНЬ
class Term:
    def __init__(self, name, a, b, c):
        self.name = name
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)

    def membership(self, x):
        """Трикутна функція належності."""
        if x <= self.a or x >= self.c:
            return 0.0
        if x == self.b:
            return 1.0
        if x < self.b:
            return (x - self.a) / (self.b - self.a)
        return (self.c - x) / (self.c - self.b)

    def to_dict(self):
        return {
            "name": self.name,
            "a": self.a,
            "b": self.b,
            "c": self.c
        }

    @staticmethod
    def from_dict(data):
        return Term(data["name"], data["a"], data["b"], data["c"])


class FuzzyVariable:
    def __init__(self, name, minimum, maximum):
        self.name = name
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.terms = {}

    def add_term(self, term):
        self.terms[term.name] = term

    def to_dict(self):
        return {
            "name": self.name,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "terms": [term.to_dict() for term in self.terms.values()]
        }

    @staticmethod
    def from_dict(data):
        variable = FuzzyVariable(data["name"], data["minimum"], data["maximum"])
        for term_data in data["terms"]:
            variable.add_term(Term.from_dict(term_data))
        return variable


class FuzzyRule:
    def __init__(self, light_term, motion_term, brightness_term, operator="AND"):
        self.light_term = light_term          
        self.motion_term = motion_term        
        self.brightness_term = brightness_term
        self.operator = operator              

    def to_dict(self):
        return {
            "light": self.light_term,
            "motion": self.motion_term,
            "brightness": self.brightness_term,
            "operator": self.operator
        }

    @staticmethod
    def from_dict(data):
        return FuzzyRule(
            data["light"],
            data["motion"],
            data["brightness"],
            data.get("operator", "AND")
        )

# СТВОРЕННЯ ПОЧАТКОВОЇ БАЗИ ЗНАНЬ (ОСВІТЛЕННЯ ТА РУХ)
def create_default_database():
    light = FuzzyVariable("Природне світло", 0, 1000)
    light.add_term(Term("Низьке", 0, 0, 400))
    light.add_term(Term("Помірне", 300, 500, 700))
    light.add_term(Term("Яскраве", 600, 1000, 1000))

    motion = FuzzyVariable("Рух", 0, 100)
    motion.add_term(Term("Відсутній", 0, 0, 40))
    motion.add_term(Term("Слабкий", 20, 50, 80))
    motion.add_term(Term("Активний", 60, 100, 100))

    brightness = FuzzyVariable("Яскравість освітлення", 0, 100)
    brightness.add_term(Term("Вимкнено", 0, 0, 30))
    brightness.add_term(Term("Середня", 20, 50, 80))
    brightness.add_term(Term("Максимальна", 70, 100, 100))

    rules = [
        FuzzyRule("Низьке", "Активний", "Максимальна", "AND"),
        FuzzyRule("Низьке", "Слабкий", "Середня", "AND"),
        FuzzyRule("Яскраве", None, "Вимкнено", "AND"),            
        FuzzyRule(None, "Відсутній", "Вимкнено", "AND"),          
        FuzzyRule("Помірне", "Активний", "Середня", "OR"),        
        FuzzyRule("Низьке", "Слабкий", "Максимальна", "OR")       
    ]

    variables = {
        "Природне світло": light,
        "Рух": motion,
        "Яскравість освітлення": brightness
    }
    return variables, rules

# НЕЧІТКИЙ ВИСНОВОК МAМДАНІ З ПІДТРИМКОЮ ГНУЧКИХ ПРАВИЛ
def fuzzy_inference(variables, rules, light_value, motion_value):
    light = variables["Природне світло"]
    motion = variables["Рух"]
    brightness = variables["Яскравість освітлення"]

    light_memberships = {name: term.membership(light_value) for name, term in light.terms.items()}
    motion_memberships = {name: term.membership(motion_value) for name, term in motion.terms.items()}

    aggregated = {name: 0.0 for name in brightness.terms}

    for rule in rules:
        degrees = []
        if rule.light_term:
            degrees.append(light_memberships.get(rule.light_term, 0.0))
        if rule.motion_term:
            degrees.append(motion_memberships.get(rule.motion_term, 0.0))

        if not degrees:
            activation = 0.0
        elif len(degrees) == 1:
            activation = degrees[0]
        else:
            if rule.operator == "OR":
                activation = max(degrees)
            else:
                activation = min(degrees)

        aggregated[rule.brightness_term] = max(aggregated[rule.brightness_term], activation)

    numerator = 0.0
    denominator = 0.0
    steps = 200
    for i in range(steps + 1):
        x = brightness.minimum + i * (brightness.maximum - brightness.minimum) / steps
        degree = 0.0
        for term_name, activation in aggregated.items():
            term = brightness.terms[term_name]
            clipped = min(activation, term.membership(x))
            degree = max(degree, clipped)
        numerator += x * degree
        denominator += degree

    result = 0.0 if denominator == 0 else numerator / denominator
    return result, aggregated

# ГРАФІЧНИЙ РЕДАКТОР
class FuzzyEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Редактор нечіткої бази знань (Варіант 4)")
        self.geometry("1150x750")
        self.minsize(1000, 650)
        self.variables, self.rules = create_default_database()
        self.create_interface()
        self.refresh_all()

    def create_interface(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Нова база", command=self.new_database)
        file_menu.add_command(label="Відкрити", command=self.load_database)
        file_menu.add_command(label="Зберегти", command=self.save_database)
        file_menu.add_separator()
        file_menu.add_command(label="Вихід", command=self.destroy)
        menu.add_cascade(label="Файл", menu=file_menu)
        self.config(menu=menu)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Ліва панель (Змінні)
        left = ttk.LabelFrame(main, text="Структура бази знань")
        left.pack(side="left", fill="y", padx=(0, 10))

        self.variable_list = tk.Listbox(left, width=25, height=15, exportselection=False)
        self.variable_list.pack(padx=10, pady=10)
        self.variable_list.bind("<<ListboxSelect>>", self.variable_selected)

        ttk.Button(left, text="Оновити", command=self.refresh_variables).pack(fill="x", padx=10, pady=5)

        # Центральна область
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True)

        term_frame = ttk.LabelFrame(center, text="Терми та функція належності")
        term_frame.pack(fill="x", pady=(0, 10))

        self.term_list = tk.Listbox(term_frame, height=5, exportselection=False)
        self.term_list.grid(row=0, column=0, rowspan=5, padx=10, pady=10)
        self.term_list.bind("<<ListboxSelect>>", self.term_selected)

        ttk.Label(term_frame, text="Параметр a").grid(row=0, column=1)
        ttk.Label(term_frame, text="Параметр b").grid(row=1, column=1)
        ttk.Label(term_frame, text="Параметр c").grid(row=2, column=1)

        self.a_entry = ttk.Entry(term_frame, width=12)
        self.b_entry = ttk.Entry(term_frame, width=12)
        self.c_entry = ttk.Entry(term_frame, width=12)

        self.a_entry.grid(row=0, column=2, padx=5, pady=3)
        self.b_entry.grid(row=1, column=2, padx=5, pady=3)
        self.c_entry.grid(row=2, column=2, padx=5, pady=3)

        ttk.Button(term_frame, text="Застосувати", command=self.update_term).grid(row=3, column=1, columnspan=2, pady=8)

        # Таблиця правил
        rule_frame = ttk.LabelFrame(center, text="База нечітких правил")
        rule_frame.pack(fill="both", expand=True)

        columns = ("light", "operator", "motion", "brightness")
        self.rule_tree = ttk.Treeview(rule_frame, columns=columns, show="headings", height=10)
        self.rule_tree.heading("light", text="Природне світло")
        self.rule_tree.heading("operator", text="Оператор")
        self.rule_tree.heading("motion", text="Рух")
        self.rule_tree.heading("brightness", text="Яскравість освітлення")

        self.rule_tree.column("light", width=140)
        self.rule_tree.column("operator", width=80)
        self.rule_tree.column("motion", width=140)
        self.rule_tree.column("brightness", width=160)

        self.rule_tree.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = ttk.Frame(rule_frame)
        buttons.pack(pady=5)
        ttk.Button(buttons, text="Додати правило", command=self.add_rule).pack(side="left", padx=5)
        ttk.Button(buttons, text="Видалити правило", command=self.delete_rule).pack(side="left", padx=5)

        # Нижня панель
        bottom = ttk.LabelFrame(self, text="Нечіткий висновок")
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(bottom, text="Світло (lux):").grid(row=0, column=0, padx=5, pady=10)
        self.light_entry = ttk.Entry(bottom, width=10)
        self.light_entry.insert(0, "200")
        self.light_entry.grid(row=0, column=1)

        ttk.Label(bottom, text="Рух (%):").grid(row=0, column=2, padx=5)
        self.motion_entry = ttk.Entry(bottom, width=10)
        self.motion_entry.insert(0, "70")
        self.motion_entry.grid(row=0, column=3)

        ttk.Button(bottom, text="Запустити висновок", command=self.run_inference).grid(row=0, column=4, padx=15)
        self.result_label = ttk.Label(bottom, text="Результат: —", font=("Arial", 12, "bold"))
        self.result_label.grid(row=0, column=5, padx=15)

    def refresh_all(self):
        self.refresh_variables()
        self.refresh_rules()

    def refresh_variables(self):
        self.variable_list.delete(0, tk.END)
        for name in self.variables:
            self.variable_list.insert(tk.END, name)
        if self.variable_list.size() > 0:
            self.variable_list.selection_set(0)
            self.show_terms()

    def variable_selected(self, event=None):
        self.show_terms()

    def show_terms(self):
        self.term_list.delete(0, tk.END)
        selection = self.variable_list.curselection()
        if not selection:
            if self.variable_list.size() > 0:
                self.variable_list.selection_set(0)
                selection = self.variable_list.curselection()
            if not selection:
                return
        
        name = self.variable_list.get(selection[0])
        variable = self.variables[name]
        for term_name in variable.terms:
            self.term_list.insert(tk.END, term_name)
        
        # Автоматично виділяємо перший терм, щоб поля заповнювалися одразу
        if self.term_list.size() > 0:
            self.term_list.selection_set(0)
            self.term_selected()

    def term_selected(self, event=None):
        selection = self.variable_list.curselection()
        term_selection = self.term_list.curselection()
        
        if not selection:
            if self.variable_list.size() > 0:
                self.variable_list.selection_set(0)
                selection = self.variable_list.curselection()
        if not term_selection:
            if self.term_list.size() > 0:
                self.term_list.selection_set(0)
                term_selection = self.term_list.curselection()
                
        if not selection or not term_selection:
            return

        variable_name = self.variable_list.get(selection[0])
        term_name = self.term_list.get(term_selection[0])
        
        if variable_name not in self.variables or term_name not in self.variables[variable_name].terms:
            return

        term = self.variables[variable_name].terms[term_name]
        
        self.a_entry.delete(0, tk.END)
        self.a_entry.insert(0, str(term.a))
        self.b_entry.delete(0, tk.END)
        self.b_entry.insert(0, str(term.b))
        self.c_entry.delete(0, tk.END)
        self.c_entry.insert(0, str(term.c))

    def refresh_rules(self):
        for item in self.rule_tree.get_children():
            self.rule_tree.delete(item)
        for index, rule in enumerate(self.rules):
            light_str = rule.light_term if rule.light_term else "[Ігнорувати]"
            motion_str = rule.motion_term if rule.motion_term else "[Ігнорувати]"
            op_str = rule.operator if (rule.light_term and rule.motion_term) else "—"
            self.rule_tree.insert("", tk.END, iid=str(index), values=(light_str, op_str, motion_str, rule.brightness_term))

    def update_term(self):
        selection = self.variable_list.curselection()
        term_selection = self.term_list.curselection()
        if not selection or not term_selection:
            messagebox.showwarning("Попередження", "Оберіть змінну та терм.")
            return
        try:
            a = float(self.a_entry.get())
            b = float(self.b_entry.get())
            c = float(self.c_entry.get())
        except ValueError:
            messagebox.showerror("Помилка", "Параметри повинні бути числами.")
            return
        if not (a <= b <= c):
            messagebox.showerror("Помилка", "Має виконуватися умова a ≤ b ≤ c.")
            return

        variable_name = self.variable_list.get(selection[0])
        term_name = self.term_list.get(term_selection[0])
        term = self.variables[variable_name].terms[term_name]
        term.a, term.b, term.c = a, b, c
        messagebox.showinfo("Редактор", "Параметри терму оновлено.")

    def add_rule(self):
        dialog = tk.Toplevel(self)
        dialog.title("Додавання правила (Варіант 4)")
        dialog.geometry("380x320")

        light_terms = ["[Ігнорувати]"] + list(self.variables["Природне світло"].terms.keys())
        motion_terms = ["[Ігнорувати]"] + list(self.variables["Рух"].terms.keys())
        brightness_terms = list(self.variables["Яскравість освітлення"].terms.keys())

        ttk.Label(dialog, text="Природне світло:").pack(pady=(10, 2))
        light_box = ttk.Combobox(dialog, values=light_terms, state="readonly")
        light_box.pack()

        ttk.Label(dialog, text="Логічний оператор:").pack(pady=(8, 2))
        operator_box = ttk.Combobox(dialog, values=["AND (І)", "OR (АБО)"], state="readonly")
        operator_box.pack()

        ttk.Label(dialog, text="Рух:").pack(pady=(8, 2))
        motion_box = ttk.Combobox(dialog, values=motion_terms, state="readonly")
        motion_box.pack()

        ttk.Label(dialog, text="Яскравість освітлення (Вихід):").pack(pady=(8, 2))
        brightness_box = ttk.Combobox(dialog, values=brightness_terms, state="readonly")
        brightness_box.pack()

        light_box.current(1)
        operator_box.current(0)
        motion_box.current(1)
        brightness_box.current(0)

        def save_rule():
            l_val = None if light_box.get() == "[Ігнорувати]" else light_box.get()
            m_val = None if motion_box.get() == "[Ігнорувати]" else motion_box.get()
            op_val = "OR" if "OR" in operator_box.get() else "AND"

            if l_val is None and m_val is None:
                messagebox.showerror("Помилка", "Принаймні одна вхідна умова повинна бути вибрана.")
                return

            rule = FuzzyRule(l_val, m_val, brightness_box.get(), op_val)
            self.rules.append(rule)
            self.refresh_rules()
            dialog.destroy()

        ttk.Button(dialog, text="Додати", command=save_rule).pack(pady=15)

    def delete_rule(self):
        selection = self.rule_tree.selection()
        if not selection:
            messagebox.showwarning("Попередження", "Оберіть правило.")
            return
        index = int(selection[0])
        del self.rules[index]
        self.refresh_rules()

    def run_inference(self):
        try:
            light_val = float(self.light_entry.get())
            motion_val = float(self.motion_entry.get())
        except ValueError:
            messagebox.showerror("Помилка", "Введіть числові значення.")
            return

        if not (0 <= light_val <= 1000):
            messagebox.showerror("Помилка", "Світло повинно бути від 0 до 1000 lux.")
            return
        if not (0 <= motion_val <= 100):
            messagebox.showerror("Помилка", "Рух повинен бути від 0 до 100 %.")
            return

        result, aggregated = fuzzy_inference(self.variables, self.rules, light_val, motion_val)
        self.result_label.config(text=f"Результат: {result:.2f} %")

        details = "\n".join(f"{name}: {value:.3f}" for name, value in aggregated.items())
        messagebox.showinfo("Результат висновку", f"Яскравість освітлення: {result:.2f} %\n\nСтупені активації:\n{details}")

    def new_database(self):
        self.variables, self.rules = create_default_database()
        self.refresh_all()

    def save_database(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON-файли", "*.json")])
        if not filename:
            return
        data = {
            "variables": [variable.to_dict() for variable in self.variables.values()],
            "rules": [rule.to_dict() for rule in self.rules]
        }
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            messagebox.showinfo("Збереження", "Базу знань успішно збережено.")
        except Exception as error:
            messagebox.showerror("Помилка", str(error))

    def load_database(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON-файли", "*.json")])
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.variables = {v["name"]: FuzzyVariable.from_dict(v) for v in data["variables"]}
            self.rules = [FuzzyRule.from_dict(r) for r in data["rules"]]
            self.refresh_all()
            messagebox.showinfo("Завантаження", "Базу знань успішно завантажено.")
        except Exception as error:
            messagebox.showerror("Помилка", f"Не вдалося завантажити файл:\n{error}")

if __name__ == "__main__":
    app = FuzzyEditor()
    app.mainloop()