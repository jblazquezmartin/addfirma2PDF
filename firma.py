import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import datetime

# Variables globales para la firma y los datos
firma_image = None
nombre = ""
dni = ""
apellidos=""

# Clase para la captura de la firma
class CapturaFirma:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Captura de Firma")

        # Inicializar el lienzo de captura
        self.lienzo = tk.Canvas(ventana, bg="white", width=400, height=200)
        self.lienzo.pack()

        # Etiqueta y campo de entrada para el nombre
        self.etiqueta_nombre = tk.Label(ventana, text="Nombre:")
        self.entrada_nombre = tk.Entry(ventana)
        self.etiqueta_nombre.pack()
        self.entrada_nombre.pack()

        # Etiqueta y campo de entrada para apellidos
        self.etiqueta_apellidos = tk.Label(ventana, text="Apellidos:")
        self.entrada_apellidos = tk.Entry(ventana)
        self.etiqueta_apellidos.pack()
        self.entrada_apellidos.pack()

        # Etiqueta y campo de entrada para el DNI
        self.etiqueta_dni = tk.Label(ventana, text="DNI:")
        self.entrada_dni = tk.Entry(ventana)
        self.etiqueta_dni.pack()
        self.entrada_dni.pack()
        

        # Crear botones para guardar y borrar la firma
        self.boton_guardar = tk.Button(ventana, text="Guardar Firma", command=self.guardar_firma)
        self.boton_borrar = tk.Button(ventana, text="Borrar", command=self.borrar_firma)

        self.boton_guardar.pack()
        self.boton_borrar.pack()

        # Inicializar el objeto ImageDraw para dibujar
        self.dibujar = Image.new("RGB", (400, 200), "white")
        self.dibujar_lienzo = ImageDraw.Draw(self.dibujar)

        self.iniciar_captura()

    def iniciar_captura(self):
        self.lienzo.bind("<Button-1>", self.iniciar_trazo)
        self.lienzo.bind("<B1-Motion>", self.dibujar_trazo)
        self.lienzo.bind("<ButtonRelease-1>", self.detener_trazo)
        self.ultimo_x = None
        self.ultimo_y = None

    def iniciar_trazo(self, evento):
        self.ultimo_x = evento.x
        self.ultimo_y = evento.y

    def dibujar_trazo(self, evento):
        x, y = evento.x, evento.y
        if self.ultimo_x and self.ultimo_y:
            self.lienzo.create_line((self.ultimo_x, self.ultimo_y, x, y), width=2, fill="black")
            self.dibujar_lienzo.line([(self.ultimo_x, self.ultimo_y), (x, y)], fill="black", width=2)
        self.ultimo_x = x
        self.ultimo_y = y

    def detener_trazo(self, evento):
        self.ultimo_x = None
        self.ultimo_y = None

    def guardar_firma(self):
        global firma_image, nombre, dni, apellidos
        firma_image = self.dibujar.copy()  # Copia la imagen dibujada
        nombre = self.entrada_nombre.get()  # Obtiene el nombre ingresado
        apellidos = self.entrada_apellidos.get()  # Obtiene los apellidos
        dni = self.entrada_dni.get()  # Obtiene el DNI ingresado
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Obtener la fecha actual    
        firma_image.save("firma.png")  # Guarda la firma en "firma.png"
        with open("fecha.txt", "w") as archivo_fecha: # Guardar la fecha actual
            archivo_fecha.write(fecha_actual)
        self.ventana.destroy()

    def borrar_firma(self):
        self.lienzo.delete("all")
        self.dibujar = Image.new("RGB", (400, 200), "white")
        self.dibujar_lienzo = ImageDraw.Draw(self.dibujar)

# Función para agregar la firma y datos a un archivo PDF
def agregar_firma_a_pdf(pdf_file, pdf_file_con_firma):
    firma_bytes = None

    if firma_image:
        # Convertir la imagen "firma.png" a bytes
        firma_byte_array = io.BytesIO()
        firma_image_resized = firma_image.resize((firma_image.width // 4, firma_image.height // 4))  # Redimensionar la imagen
        firma_image_resized.save(firma_byte_array, format='PNG')
        firma_bytes = firma_byte_array.getvalue()

    pdf_document = fitz.open(pdf_file)  # Abre el archivo PDF
    firma_page = None

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        page_width = page.rect.width  # Ancho de la página
        page_height = page.rect.height  # Alto de la página
        if firma_bytes:
            # Insertar la imagen de la firma en el borde inferior
            rect = fitz.Rect(page.rect.width - firma_image.width // 4, page.rect.height - firma_image.height // 4,
                             page.rect.width, page.rect.height)
            page.insert_image(rect, stream=firma_bytes)

        if page_num == len(pdf_document) - 1 and firma_bytes:
            # Agregar nombre y DNI en el lado contrario a la firma
            page_width = page.rect.width
            page_height = page.rect.height
            rect_texto = fitz.Rect(10, page_height - 40, page_width - 10, page_height)
            texto_firma = f"Nombre: {nombre} {apellidos}\nDNI: {dni}"
            page.insert_textbox(rect_texto, texto_firma, fontsize=10, align=0)

            firma_page = page

        # Obtener la fecha actual
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Agregar fecha debajo de la firma en el lado contrario a los datos
        rect_fecha = fitz.Rect(10, page_height - 60, page_width - 10, page_height - 40)
        texto_fecha = f"Fecha: {fecha_actual}"
        page.insert_textbox(rect_fecha, texto_fecha, fontsize=10, align=0)    

    if firma_page:
        pdf_document.save(pdf_file_con_firma)
    else:
        pdf_document.close()
        raise ValueError("No se pudo agregar la firma al PDF")

if __name__ == "__main__":
    # Crear ventana para captura de firma
    root = tk.Tk()
    app = CapturaFirma(root)
    root.mainloop()

    # Luego de que se capture la firma y los datos, seleccionar el archivo PDF original
    pdf_file = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])

    # Ruta del archivo PDF resultante con la firma y los datos
    pdf_file_con_firma = "documento_firmado.pdf"

    # Agregar la firma y los datos al PDF
    agregar_firma_a_pdf(pdf_file, pdf_file_con_firma)

    print("Firma y datos agregados al PDF correctamente.")
