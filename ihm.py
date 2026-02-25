from customtkinter import * 
import tkinter
import requests

def send_request(ip, port=80, endpoint="/"):
    try:
        url = f"http://{ip}:{port}{endpoint}"
        response = requests.get(url, timeout=5)
        print(response, "test")
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
        header.pack(pady=(0,10))

        main_frame = tkinter.Frame(self)
        main_frame.pack(fill="both", expand=True)

        left = tkinter.Frame(main_frame, bd=1, relief="sunken", width=200)
        left.pack(side="left", fill="y", padx=(0,10))
        right = tkinter.Frame(main_frame, bd=1, relief="sunken")
        right.pack(side="left", fill="both", expand=True)

        tkinter.Label(left, text="Navigation").pack(pady=5)
        for i in range(1,5):
            btn = tkinter.Button(left, text=f"Option {i}", command=lambda i=i: self.on_nav(i))
            btn.pack(fill="x", padx=5, pady=2)

        buttontest = tkinter.Button(left, text="Test API", command=lambda: send_request(ip="172.20.10.5", port=5000, endpoint="/ajouter_une_carte"))
        buttontest.pack(fill="x", padx=5, pady=2)

        tkinter.Label(right, text="Contenu").pack(anchor="nw")
        self.content = tkinter.Text(right)
        self.content.pack(fill="both", expand=True, padx=5, pady=5)

        footer = tkinter.Frame(self)
        footer.pack(fill="x", pady=(10,0))
        tkinter.Button(footer, text="Quitter", command=self.quit).pack(side="right")

    def on_nav(self, idx):
        self.content.delete("1.0", "end")
        self.content.insert("1.0", f"Contenu pour l'option {idx}")

if __name__ == "__main__":
    app = App()
    app.mainloop()