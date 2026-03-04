import tkinter
from tkinter import messagebox
import requests


def send_request(ip, port=80, endpoint="/", valeur={"erreur": "erreur"}):
    try:
        if valeur == {"erreur": "erreur"}: 
            url = f"http://{ip}:{port}{endpoint}"
            response = requests.get(url, timeout=5)
            return response.text
        else:
            url = f"http://{ip}:{port}{endpoint}"
            response = requests.post(url, timeout=5, json=valeur)
            return response.text
            
    except requests.exceptions.RequestException as e:
        return f"Erreur: {str(e)}"
    

class App(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title("Maquette Sûreté")
        self.geometry("800x600")
        self.configure(padx=10, pady=10)
        self._create_widgets()

    def _create_widgets(self):
        header = tkinter.Label(self, text="Maquette système sûreté", font=("Arial", 18))
        header.pack(pady=(0, 10))

        main_frame = tkinter.Frame(self)
        main_frame.pack(fill="both", expand=True)

        left = tkinter.Frame(main_frame, bd=1, relief="sunken", width=200)
        left.pack(side="left", fill="y", padx=(0, 10))
        right = tkinter.Frame(main_frame, bd=1, relief="sunken")
        right.pack(side="left", fill="both", expand=True)

        tkinter.Label(left, text="Navigation").pack(pady=5)

        def on_api_response():
            response = send_request(ip="172.20.10.2", port=5000, endpoint="/ajouter_une_carte")
            self.content.delete("1.0", "end")
            self.content.insert("1.0", response)

        def on_view_cards():
            self.show_card_selection_window()

        def on_modify_card():
            modify_window = tkinter.Toplevel(self)
            modify_window.title("Modifier une carte")
            modify_window.geometry("400x300")
        
            tkinter.Label(modify_window, text="ID Badge:").pack(pady=5)
            id_entry = tkinter.Entry(modify_window)
            id_entry.pack(fill="x", padx=10)
            
            tkinter.Label(modify_window, text="Texte:").pack(pady=5)
            text_entry = tkinter.Entry(modify_window)
            text_entry.pack(fill="x", padx=10)
            
            tkinter.Label(modify_window, text="ID Utilisateur:").pack(pady=5)
            user_entry = tkinter.Entry(modify_window)
            user_entry.pack(fill="x", padx=10)
        
            def submit():
                data = {
                    "id": id_entry.get(),
                    "texte": text_entry.get(),
                    "id_util": user_entry.get()
                }
                response = send_request(ip="172.20.10.2", port=5000, 
                                    endpoint=f"/modifier_une_carte/{id_entry.get()}", 
                                    valeur=data)
                self.content.delete("1.0", "end")
                self.content.insert("1.0", response)
                modify_window.destroy()
            
            tkinter.Button(modify_window, text="Valider", command=submit).pack(pady=10)

        #Création de bouton permettant d'intéragir avec la base de données
        tkinter.Button(left, text="Ajouter une carte", command=on_api_response).pack(fill="x", padx=5, pady=2)
        tkinter.Button(left, text="Voir les cartes", command=on_view_cards).pack(fill="x", padx=5, pady=2)
        tkinter.Button(left, text="Modifier une carte", command=on_modify_card).pack(fill="x", padx=5, pady=2)

        tkinter.Label(right, text="Contenu").pack(anchor="nw")
        self.content = tkinter.Text(right)
        self.content.pack(fill="both", expand=True, padx=5, pady=5)

        footer = tkinter.Frame(self)
        footer.pack(fill="x", pady=(10, 0))
        tkinter.Button(footer, text="Quitter", command=self.quit).pack(side="right")

    def show_card_selection_window(self):
        response = send_request(ip="172.20.10.2", port=5000, endpoint="/afficher_cartes")
        
        try:
            import json
            cards = json.loads(response)
        except:
            messagebox.showerror("Erreur", f"Impossible de récupérer les cartes: {response}")
            return
        
        selection_window = tkinter.Toplevel(self)
        selection_window.title("Sélectionner une carte")
        selection_window.geometry("500x400")
        
        tkinter.Label(selection_window, text="Cartes disponibles:", font=("Arial", 12)).pack(pady=5)
        
        frame = tkinter.Frame(selection_window)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = tkinter.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tkinter.Listbox(frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        for card in cards:
            listbox.insert(tkinter.END, str(card))
        
        def on_select():
            if listbox.curselection():
                self.content.delete("1.0", "end")
                self.content.insert("1.0", str(cards[listbox.curselection()[0]]))
                selection_window.destroy()
        
        tkinter.Button(selection_window, text="Sélectionner", command=on_select).pack(pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()
