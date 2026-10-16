"""Optional Tkinter UI. No local server. GPL-3.0-or-later."""

import json
import queue
import threading

from . import __version__, core
from .cli import format_report, save_report


def load_owner(directory):
    root = core.checked_root(directory)
    config_file = root / ".codemark/project.json"
    return core.load_config(root)["owner"] if config_file.exists() else None


def start_worker(operation, inbox):
    """Normal interpreter shutdown waits for any in-flight file transaction."""

    def work():
        try:
            inbox.put((operation(), None))
        # Return worker failures to the main thread so the UI can report them.
        except Exception as error:  # noqa: BLE001
            inbox.put((None, str(error)))

    worker = threading.Thread(target=work, daemon=False)
    worker.start()
    return worker


def launch():
    try:
        import tkinter as tk
        from tkinter import filedialog
        from tkinter.scrolledtext import ScrolledText

        window = tk.Tk()
    except Exception as error:
        raise RuntimeError("Tkinter ou sessão gráfica indisponível") from error
    window.title("SecOps CodeMark " + __version__)
    window.geometry("940x740")
    window.minsize(760, 620)
    black, panel, cyan, white = "#080b0d", "#111a20", "#00d8ee", "#e9f2f5"
    window.configure(bg=black)
    window.option_add("*Font", "TkDefaultFont 11")
    root_path, suspect_path, owner = tk.StringVar(), tk.StringVar(), tk.StringVar()
    status = tk.StringVar(
        value="Escolha a pasta com código de sua autoria. A prévia não altera arquivos."
    )
    inbox, report = queue.Queue(), {}
    buttons = []
    busy, closing = False, False

    def label(text, size=11, color=white):
        return tk.Label(
            window,
            text=text,
            bg=black,
            fg=color,
            font=("TkDefaultFont", size),
            anchor="w",
            justify="left",
        )

    label("CODEMARK", 26, cyan).pack(anchor="w", padx=24, pady=(20, 0))
    label("Procedência para o seu código. Local, leve e reversível.", 12).pack(
        anchor="w", padx=24, pady=(0, 18)
    )

    def field(title, variable, directory=False):
        label(title, 10, cyan).pack(anchor="w", padx=24)
        row = tk.Frame(window, bg=black)
        row.pack(fill="x", padx=24, pady=(4, 12))
        entry = tk.Entry(
            row,
            textvariable=variable,
            bg=panel,
            fg=white,
            insertbackground=cyan,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#29414b",
        )
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        if directory:

            def choose():
                chosen = filedialog.askdirectory(title=title)
                if chosen:
                    if variable is root_path:
                        try:
                            chosen_owner = load_owner(chosen)
                        except core.CodeMarkError:
                            status.set(
                                "Identidade existente inválida; verifique o projeto pela CLI."
                            )
                            return
                        owner.set(chosen_owner or "")
                    variable.set(chosen)

            tk.Button(
                row,
                text="Escolher pasta",
                command=choose,
                bg=panel,
                fg=cyan,
                activebackground=cyan,
                activeforeground=black,
                relief="flat",
            ).pack(side="left", padx=(8, 0), ipady=6)

    field("PROJETO ORIGINAL", root_path, True)
    field("TITULAR INFORMADO (primeira aplicação)", owner)
    field("PASTA A COMPARAR (opcional)", suspect_path, True)
    toolbar = tk.Frame(window, bg=black)
    toolbar.pack(fill="x", padx=24, pady=(0, 12))
    text = ScrolledText(
        window,
        bg=panel,
        fg=white,
        insertbackground=cyan,
        relief="flat",
        wrap="word",
        height=14,
        font=("TkFixedFont", 10),
    )
    text.pack(fill="both", expand=True, padx=24)
    text.insert(
        "1.0",
        "1. Escolha seu projeto e informe o titular.\n2. Veja a prévia e aplique a marca.\n3. Verifique alterações ou compare uma pasta suspeita.\n\nA marca é um comentário removível. A comparação aponta indícios, não prova de plágio.\nAssinatura GPG opcional está disponível pela linha de comando.\n",
    )
    text.configure(state="disabled")
    tk.Label(
        window,
        textvariable=status,
        bg=black,
        fg=cyan,
        anchor="w",
        justify="left",
        wraplength=880,
    ).pack(fill="x", padx=24, pady=12)
    label(
        "GPL-3.0-or-later  •  Sem conexão de rede  •  Código público pode ser estudado",
        9,
    ).pack(anchor="w", padx=24, pady=(0, 16))

    def run(action):
        nonlocal busy
        if busy:
            return
        root_value, suspect_value, owner_value = (
            root_path.get().strip(),
            suspect_path.get().strip(),
            owner.get().strip(),
        )
        if not root_value or (action == "compare" and not suspect_value):
            status.set(
                "Selecione a pasta do projeto e, para comparar, a pasta suspeita."
            )
            return
        for button in buttons:
            button.configure(state="disabled")
        busy = True
        status.set("Processando fontes locais…")

        def operation():
            if action in ("preview", "mark"):
                return core.mark(
                    root_value, owner_value or None, apply=action == "mark"
                )
            if action == "verify":
                return core.verify(root_value)
            if action == "compare":
                return core.compare(root_value, suspect_value)
            return core.unmark(root_value, apply=True)

        start_worker(operation, inbox)

    for caption, action in [
        ("Prévia", "preview"),
        ("Aplicar marca", "mark"),
        ("Verificar", "verify"),
        ("Comparar", "compare"),
        ("Remover marcas", "unmark"),
    ]:
        button = tk.Button(
            toolbar,
            text=caption,
            command=lambda value=action: run(value),
            bg=cyan if action == "mark" else panel,
            fg=black if action == "mark" else cyan,
            activebackground=cyan,
            activeforeground=black,
            relief="flat",
            padx=10,
            pady=8,
        )
        button.pack(side="left", padx=(0, 6))
        buttons.append(button)

    def save():
        if not report:
            status.set("Execute uma operação para gerar um relatório.")
            return
        destination = filedialog.asksaveasfilename(
            defaultextension=".json", title="Salvar relatório em arquivo novo"
        )
        if destination:
            try:
                save_report(
                    destination,
                    json.dumps(report, ensure_ascii=True, indent=2),
                    (root_path.get(), suspect_path.get()),
                )
                status.set("Relatório salvo.")
            except core.CodeMarkError as error:
                status.set(str(error))

    tk.Button(
        toolbar,
        text="Salvar",
        command=save,
        bg=panel,
        fg=cyan,
        relief="flat",
        padx=10,
        pady=8,
    ).pack(side="right")

    def poll():
        nonlocal report, busy
        try:
            result, error = inbox.get_nowait()
        except queue.Empty:
            window.after(100, poll)
            return
        for button in buttons:
            button.configure(state="normal")
        busy = False
        text.configure(state="normal")
        text.delete("1.0", "end")
        if error:
            text.insert("1.0", "Erro: " + error)
            status.set("Operação não concluída; confira o relatório.")
        else:
            report = result
            text.insert("1.0", format_report(result))
            status.set("Operação concluída. Confira a cobertura e os resultados acima.")
        text.configure(state="disabled")
        if closing:
            window.destroy()
        else:
            window.after(100, poll)

    def close_window():
        nonlocal closing
        if busy:
            closing = True
            status.set("Aguardando a operação concluir antes de fechar…")
        else:
            window.destroy()

    window.protocol("WM_DELETE_WINDOW", close_window)
    window.after(100, poll)
    window.mainloop()
