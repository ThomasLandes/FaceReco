import os
import face_recognition
import cv2
from tkinter import Tk, Label, Button, Entry, Listbox, Scrollbar, Toplevel, messagebox

# Dossier contenant les images des étudiants
IMAGE_DIR = "C:/Temp/images"
DEBIT_AMOUNT = 5.50  # Montant à débiter par passage

# Charger les encodages des visages des étudiants
def load_student_faces(image_dir):
    student_faces = {}
    for file_name in os.listdir(image_dir):
        if file_name.endswith(('.jpg', '.png')):
            student_id = file_name.split("_")[0]
            name = "_".join(file_name.split("_")[1:]).split(".")[0]
            image_path = os.path.join(image_dir, file_name)
            image = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(image)
            if encoding:  # S'assurer qu'un visage a été détecté
                student_faces[student_id] = {
                    "name": name,
                    "encoding": encoding[0],
                    "balance": 10.0  # Solde pour chaque étudiant
                }
    return student_faces

# Sauvegarder un nouvel étudiant
def save_new_student(name, image):
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    # Déterminer le prochain ID
    existing_ids = [int(f.split("_")[0]) for f in os.listdir(IMAGE_DIR) if f.split("_")[0].isdigit()]
    new_id = max(existing_ids, default=0) + 1
    file_name = f"{new_id}_{name}.jpg"
    file_path = os.path.join(IMAGE_DIR, file_name)
    cv2.imwrite(file_path, image)
    return f"Étudiant {name} ajouté avec l'ID {new_id}"

# Comparer une image en direct avec la banque d'images
def recognize_and_debit(frame, student_faces, debited_ids):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    recognized_results = []

    for face_encoding in face_encodings:
        for student_id, data in student_faces.items():
            matches = face_recognition.compare_faces([data["encoding"]], face_encoding)
            if matches[0]:
                if student_id not in debited_ids:
                    if student_faces[student_id]["balance"] >= DEBIT_AMOUNT:
                        student_faces[student_id]["balance"] -= DEBIT_AMOUNT
                        debited_ids.add(student_id)  # Marquer comme débité
                        recognized_results.append((f"{data['name']} debite {DEBIT_AMOUNT}€", (0, 255, 0)))  # Vert
                    else:
                        recognized_results.append((f"{data['name']} : solde insuffisant", (0, 0, 255)))  # Rouge
                else:
                    recognized_results.append((f"{data['name']} deja debite", (0, 255, 0)))  # Vert
                break
        else:
            recognized_results.append(("Inconnu", (255, 255, 255)))  # Blanc

    return recognized_results

# Interface graphique avec Tkinter
def main():
    # Charger les visages des étudiants
    student_faces = load_student_faces(IMAGE_DIR)

    if not student_faces:
        print("Aucune image étudiante chargée.")

    def refresh_student_list():
        student_list.delete(0, 'end')
        for student_id, data in student_faces.items():
            student_list.insert('end', f"ID: {student_id} - Nom: {data['name']} - Solde: {data['balance']}€")

    def add_new_student():
        global frame, captured_frame
        frame = None
        captured_frame = None

        def capture_photo():
            global captured_frame
            captured_frame = frame.copy()
            messagebox.showinfo("Succès", "Photo capturée. Cliquez sur 'Enregistrer' pour terminer.")

        def save_student():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Erreur", "Veuillez entrer un nom complet.")
                return
            if captured_frame is None:
                messagebox.showerror("Erreur", "Veuillez capturer une photo avant d'enregistrer.")
                return
            student_message = save_new_student(name, captured_frame)
            messagebox.showinfo("Succès", student_message)
            nonlocal student_faces
            student_faces = load_student_faces(IMAGE_DIR)
            refresh_student_list()
            cap.release()
            cv2.destroyAllWindows()
            add_window.destroy()

        def close_camera():
            cap.release()
            cv2.destroyAllWindows()
            add_window.destroy()

        add_window = Toplevel(root)
        add_window.title("Ajouter un nouvel étudiant")
        add_window.protocol("WM_DELETE_WINDOW", close_camera)

        Label(add_window, text="Nom et Prénom :").pack(pady=10)
        name_entry = Entry(add_window)
        name_entry.pack(pady=10)
        Button(add_window, text="Capturer la photo", command=capture_photo).pack(pady=10)
        Button(add_window, text="Enregistrer", command=save_student).pack(pady=10)
        Button(add_window, text="Annuler", command=close_camera).pack(pady=10)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d'accéder à la webcam.")
            add_window.destroy()
            return

        def update_camera():
            global frame
            ret, frame = cap.read()
            if ret:
                cv2.imshow("Capture de photo", frame)
                cv2.waitKey(1)
            add_window.after(10, update_camera)

        update_camera()

    def delete_student():
        selected = student_list.curselection()
        if not selected:
            messagebox.showerror("Erreur", "Veuillez sélectionner un étudiant à supprimer.")
            return
        selected_text = student_list.get(selected[0])
        student_id = selected_text.split(" - ")[0].replace("ID: ", "").strip()
        if student_id in student_faces:
            file_name = f"{student_id}_{student_faces[student_id]['name']}.jpg"
            file_path = os.path.join(IMAGE_DIR, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            del student_faces[student_id]
            messagebox.showinfo("Succès", f"L'étudiant avec l'ID {student_id} a été supprimé.")
            refresh_student_list()
        else:
            messagebox.showerror("Erreur", "Étudiant introuvable.")

    def recharge_balance():
        def recharge():
            student_id = id_entry.get().strip()
            amount = float(amount_entry.get().strip())
            if student_id in student_faces:
                student_faces[student_id]["balance"] += amount
                messagebox.showinfo("Succès", f"Le solde de {student_faces[student_id]['name']} a été rechargé de {amount}€.")
                refresh_student_list()
                recharge_window.destroy()
            else:
                messagebox.showerror("Erreur", "ID invalide.")

        recharge_window = Toplevel(root)
        recharge_window.title("Recharger un solde")
        Label(recharge_window, text="ID de l'étudiant :").pack(pady=10)
        id_entry = Entry(recharge_window)
        id_entry.pack(pady=10)
        Label(recharge_window, text="Montant à ajouter :").pack(pady=10)
        amount_entry = Entry(recharge_window)
        amount_entry.pack(pady=10)
        Button(recharge_window, text="Recharger", command=recharge).pack(pady=20)

    def live_recognition():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d'accéder à la webcam.")
            return
        debited_ids = set()
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            if frame_count % 10 == 0:
                recognized_results = recognize_and_debit(small_frame, student_faces, debited_ids)
            for i, (name, color) in enumerate(recognized_results):
                cv2.putText(frame, name, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.imshow("Reconnaissance en direct", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty("Reconnaissance en direct", cv2.WND_PROP_VISIBLE) < 1:
                break
            frame_count += 1
        cap.release()
        cv2.destroyAllWindows()
        refresh_student_list()

    root = Tk()
    root.title("Reconnaissance Faciale Simplifiée")

    Label(root, text="Reconnaissance faciale en direct").pack(pady=10)
    Button(root, text="Lancer la reconnaissance en direct", command=live_recognition).pack(pady=10)
    Button(root, text="Ajouter un nouvel étudiant", command=add_new_student).pack(pady=10)
    Button(root, text="Supprimer un étudiant", command=delete_student).pack(pady=10)
    Button(root, text="Recharger un solde", command=recharge_balance).pack(pady=10)

    Label(root, text="Liste des étudiants enregistrés :").pack(pady=10)
    scrollbar = Scrollbar(root)
    scrollbar.pack(side='right', fill='y')
    student_list = Listbox(root, yscrollcommand=scrollbar.set, width=50, height=10)
    student_list.pack(pady=10)
    scrollbar.config(command=student_list.yview)

    refresh_student_list()
    root.mainloop()

if __name__ == "__main__":
    main()
